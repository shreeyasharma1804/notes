"""
A single-threaded event loop built on epoll, with timer, disk IO and network IO futures.

Design decisions:
    1. Workers only yeild a future, i.e, a future is the only awaitable object
    2. Client Pool is used by the NetworkFuture
    3. The SSL Connection is non-blocking
"""

import os
import queue
import select
import socket
import ssl
import time
from abc import ABC, abstractmethod
from enum import IntEnum
from queue import Queue
from threading import Thread

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = "httpbin.org"
PORT = 443
REQUEST_PATH = "/delay/25"

# Should a seperate thread monitor the pool size and create more connections if required
MIN_POOL_SIZE = 5
MAX_POOL_SIZE = 10

TCP_CONNECT_TIMEOUT = 2
READ_TIMEOUT = 10
WRITE_TIMEOUT = 20

RECV_BUFFER_SIZE = 4096
TIMERFD_READ_SIZE = 8  # timerfd expirations are read as a single uint64
EPOLL_POLL_TIMEOUT = 0  # Never block the loop on epoll

DISK_IO_FILE = "/home/shreeya/test.txt"
SLEEP_TIMER = 5

# Socket interest modes, mirroring the epoll flag the socket is registered with
MODE_WRITE = "EPOLLOUT"
MODE_READ = "EPOLLIN"

# ---------------------------------------------------------------------------
# Process wide resources
# ---------------------------------------------------------------------------

# Define one epoll instance
epoll = select.epoll()

ssl_context = ssl.create_default_context()

pool = Queue()  # Thread safe, q.get() uses semaphores and locks


class ConnectionState(IntEnum):
    """
    TCP and TLS State Definitions
    """

    CONNECTING = 1
    HANDSHAKING = 2
    READY = 3
    ERROR = 4


class Connection:
    """
    Store socket state
    """

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        try:
            self.sock.settimeout(TCP_CONNECT_TIMEOUT)
            err = self.sock.connect_ex((HOST, PORT))  # Establish TCP layer connectivity
            if err:
                raise Exception
        except Exception as e:
            print(e)
            return

        self.sock = ssl_context.wrap_socket(  # TLS Handshake, but not yet
            self.sock, server_hostname=HOST, do_handshake_on_connect=False
        )
        self.state = ConnectionState.CONNECTING
        self.mode = MODE_WRITE
        self.timeout_fd = os.timerfd_create(time.CLOCK_REALTIME, flags=os.TFD_NONBLOCK)
        self.read_timeout_started = False
        self.write_timeout_started = False

    def fileno(self) -> int:
        return self.sock.fileno()


def create_pool() -> None:
    for _ in range(MAX_POOL_SIZE):
        pool.put(Connection())
    if pool.qsize() < MIN_POOL_SIZE:
        print("Pool Size is less than operational minimum")


def arm_timer(timer_fd: int, seconds: float) -> None:
    """
    Arm a one shot timerfd, which fires an EPOLLIN event on expiry
    """
    os.timerfd_settime(timer_fd, flags=0, initial=seconds, interval=0)


# ---------------------------------------------------------------------------
# Futures
# ---------------------------------------------------------------------------


class Future(ABC):
    """
    When a task does not immediately yeild the result, and is typically awaited
    """

    def __init__(self) -> None:
        self.done = False
        self.waiting_tasks = []

    @abstractmethod
    def execute_waiting_tasks(self):
        pass

    def _schedule_waiting_tasks(self, value) -> None:
        """
        Schedule every task blocked on this future back on the runnable queue,
        handing each of them the completed value
        """
        for task in self.waiting_tasks:
            loop.create_task(task, value)
        self.waiting_tasks.clear()


class SleepFuture(Future):
    """
    Expects the timer duration from the callee
    The event loop handles the timer expiry, updates the done and result variables,
    and calls execute_waiting_tasks, which schedules the tasks waiting on this future back on the runnable queue
    """

    # Executed by worker
    def __init__(self, timer) -> None:
        super().__init__()
        self.result = None
        self.timer = timer

    # Executed by Event Loop when the future is complete
    def execute_waiting_tasks(self):
        self._schedule_waiting_tasks(self.result)


class DiskIOFuture(Future):
    """
    Expects a file_location from the callee
    The event loop creates the thread to offload this disk IO to a thread,
    the thread performs the disk IO, updates the future's done and result variables,
    and calls execute_waiting_tasks to schedule the waiting tasks back on the event loop
    """

    # Executed by worker
    def __init__(self, file_location) -> None:
        super().__init__()
        self.result = None
        self.file_location = file_location

    # Executed by Event Loop when the future is complete
    def execute_waiting_tasks(self):
        self._schedule_waiting_tasks(self.result)


class NetworkIOFuture(Future):
    """
    Expects a request from the callee
    The future acquires a non blocking socket from the pool
    When an EPOLLIN or EPOLLOUT event occurs, the event loop reads/writes the data to/from the socket to the future request and response variables
    After recieving the response, the event loop calls execute_waiting_tasks to schedule the waiting tasks back on the event loop


    TODO: Healthcheck and keepalive settings at TCP layer
    """

    def __init__(self, request) -> None:
        super().__init__()
        self.request = request
        self.response = ""
        # TODO: Add healthcheck before setting the socket value in the future state
        self.connection: Connection = pool.get()
        # Register a fd and the actions on it which should trigger an event
        epoll.register(self.connection.fileno(), select.EPOLLOUT)
        self.read_timeout = READ_TIMEOUT
        self.write_timeout = WRITE_TIMEOUT
        epoll.register(self.connection.timeout_fd, select.EPOLLIN)

    def execute_waiting_tasks(self):
        if self.connection.fileno() != -1:
            print(f"Add {self.connection.fileno()} socket back to pool")
            self.connection.read_timeout_started = False
            self.connection.write_timeout_started = False
            pool.put(self.connection)  # Only if socket has not timed-out
            print(pool.__dict__)
        self._schedule_waiting_tasks(self.response)


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class Task:
    """
    A corountine is any function which yeilds
    This task is a wrapper around a coroutine, it provides the step function for the event loop to resume the coroutine execution
    """

    def __init__(self, coroutine) -> None:
        self.coroutine = coroutine  # The worker function
        self.result = None  # The worker return value
        self.exception = None  # Any exceptions

    def step(self, value=None):
        try:
            # When a worker hits yeild, it returns the future to send() object. When called
            # again with a value, it 1st sets the result of the future to value and then
            # resumes execution
            future = self.coroutine.send(value)
            return future  # Return future to event loop, so that the event loop schedules its completion
        except StopIteration as e:
            self.result = e.value  # End of execution
        except Exception as e:
            self.exception = e  # Store the exception


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------


class EventLoop:
    def __init__(self) -> None:
        self.runnable_tasks = Queue()
        self.timers = {}
        self.sockets = {}

    # -- Disk IO ------------------------------------------------------------

    def _read_file(self, file_name, future):
        """
        To execute a DiskIO future, the eventloop creates a thread with target as _read_file and starts it.
        The _read_file function reads the file, updates the future and calls execute_waiting_tasks
        """
        with open(file_name, "r") as f:
            contents = f.read()
        print("_read_file thread complete")
        future.done = True
        future.result = contents
        future.execute_waiting_tasks()

    # -- Network IO ---------------------------------------------------------

    def _fail_network_future(self, future, err):
        future.done = True
        future.connection.state = ConnectionState.ERROR
        # NOTE: typo carried over from the original, `response` is left untouched here
        future.resposne = err
        future.execute_waiting_tasks()

    def _start_network_timeout(self, future: NetworkIOFuture):
        if future.connection.mode == MODE_WRITE:
            print(
                f"WriteTimeout timer started for fd: {future.connection.fileno()} with value: {future}"
            )
            future.connection.write_timeout_started = True
            arm_timer(future.connection.timeout_fd, future.write_timeout)
        elif future.connection.mode == MODE_READ:
            print(
                f"ReadTimeout timer started for fd: {future.connection.fileno()} with value: {future.read_timeout}"
            )
            future.connection.read_timeout_started = True
            arm_timer(future.connection.timeout_fd, future.read_timeout)

    def _finish_tcp_connect(self, future: NetworkIOFuture):
        print(f"SSL Handhsake required for socket {future.connection.fileno()}")
        err = future.connection.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            self._fail_network_future(future, err)
        else:
            future.connection.state = ConnectionState.HANDSHAKING

    def _continue_tls_handshake(self, fd, future: NetworkIOFuture):
        print(f"Ongoing Handhsake for socket {future.connection.fileno()}")
        try:
            future.connection.sock.do_handshake()  # Continues from the last handshake state
            future.connection.state = ConnectionState.READY
            epoll.modify(fd, select.EPOLLOUT)
        except ssl.SSLWantReadError:  # Handshake requires reading data
            epoll.modify(fd, select.EPOLLIN)
        except ssl.SSLWantWriteError:
            epoll.modify(fd, select.EPOLLOUT)
        except Exception as e:
            self._fail_network_future(future, e)

    def _send_request(self, future: NetworkIOFuture):
        print(f"Ongoing request for socket: {future.connection.fileno()}")
        n = future.connection.sock.send(future.request.encode("utf-8"))
        future.request = future.request[n:]
        # Stop generating events of the socket being writable once writing the request is complete
        if not future.request:
            epoll.modify(future.connection.fileno(), select.EPOLLIN)
            future.connection.mode = MODE_READ
            self._start_network_timeout(future)
            print("The socket is now in response mode")

    def _receive_response(self, future: NetworkIOFuture):
        print(f"Ongoing response for socket: {future.connection.fileno()}")
        data = future.connection.sock.recv(RECV_BUFFER_SIZE)
        data = data.decode("utf-8")
        # If EPOLLIN is called with no data, the response is complete. But EPOLLIN keeps
        # getting triggered so this needs to be handled
        if not data:
            print("Response complete")
            future.done = True
            epoll.unregister(future.connection.fileno())
            future.execute_waiting_tasks()
        future.response += data

    def _transfer(self, future: NetworkIOFuture, event):
        print(f"TLS connections exists for socket {future.connection.fileno()}")
        print(f"Current socket mode: {future.connection.mode}")
        # Re-mapping the same future is a no-op, so the assignment is unconditional
        self.timers[future.connection.timeout_fd] = future
        if not future.connection.write_timeout_started:
            self._start_network_timeout(future)
        if event & select.EPOLLOUT:  # Socket is writable
            self._send_request(future)
        elif event & select.EPOLLIN:  # Socket is readable
            self._receive_response(future)

    def _handle_network_event(self, fd, event):
        future = self.sockets[fd]
        if future.connection.state == ConnectionState.CONNECTING:
            self._finish_tcp_connect(future)
        if future.connection.state == ConnectionState.HANDSHAKING:
            self._continue_tls_handshake(fd, future)
        if future.connection.state == ConnectionState.READY:
            self._transfer(future, event)

    # -- Timers -------------------------------------------------------------

    def _complete_sleep_future(self, fd, future: SleepFuture):
        print(f"SleepFuture timer complete: {fd}")
        future.done = True
        future.result = "Timer Complete"
        future.execute_waiting_tasks()
        del self.timers[fd]
        epoll.unregister(fd)
        print("Timer unregistered from epoll and event loop")

    def _expire_network_future(self, fd, future: NetworkIOFuture):
        print(f"Timer expired for future: {future}")
        if future.connection.mode == MODE_WRITE:
            print(f"Request timeout on fd: {future.connection.fileno()}")
            future.result = "Request timeout"
        else:
            print(f"Response timeout on fd: {future.connection.fileno()}")
            future.result = "Response timeout"
        future.done = True

        print(len(self.timers), len(self.sockets))

        del self.timers[fd]  # unregister the timer fd from event loop
        del self.sockets[future.connection.fileno()]  # unregister the socket fd from event loop
        epoll.unregister(fd)  # unregister the timer fd from epoll
        epoll.unregister(future.connection.fileno())  # unregister the socket fd from epoll

        print(len(self.timers), len(self.sockets))

        future.connection.sock.close()
        future.execute_waiting_tasks()

    def _handle_timer_event(self, fd):
        future = self.timers[fd]
        os.read(fd, TIMERFD_READ_SIZE)

        if isinstance(future, SleepFuture):
            self._complete_sleep_future(fd, future)
        elif isinstance(future, NetworkIOFuture):
            self._expire_network_future(fd, future)

    # -- epoll dispatch -----------------------------------------------------

    def _handle_epoll_events(self):
        """
        Handle read and write events on registered sockets, including non-blocking TLS Handshake events
        When a timer expires on a registered timer_fd, an EPOLLIN event is generated
        """

        events = epoll.poll(EPOLL_POLL_TIMEOUT)  # Poll the events on the registered fds

        for fd, event in events:
            if fd in self.timers:
                print(f"Epoll timer event: {fd}")
                self._handle_timer_event(fd)
            elif fd in self.sockets:
                print(f"Epoll network event: {fd}, event: {event}")
                self._handle_network_event(fd, event)
            else:
                continue

    # -- Scheduling ---------------------------------------------------------

    def create_task(self, task, value=None):
        """
        Add a task to the runnable queue
        """
        self.runnable_tasks.put((task, value))

    def _register_sleep_future(self, future: SleepFuture):
        """
        Create the timer_fd, call settime on it, register with epoll
        and add the timer_fd: future to self.timers
        """
        fd = os.timerfd_create(time.CLOCK_REALTIME, flags=os.TFD_NONBLOCK)
        arm_timer(fd, future.timer)
        self.timers[fd] = future
        epoll.register(fd, select.EPOLLIN)
        print(f"SleepFuture fd created: {fd}")

    def _register_disk_io_future(self, future: DiskIOFuture):
        """
        Create a thread with _read_file as the target function and start it
        _read_file completes the future and calls execute_waiting_tasks
        """
        thread = Thread(target=self._read_file, args=(future.file_location, future))
        thread.start()
        print(f"DiskIOFuture thread created: {thread}")

    def _register_network_io_future(self, future: NetworkIOFuture):
        """
        Register the socket fd with the event loop
        """
        self.sockets[future.connection.fileno()] = future
        print(
            f"NetworkIOFuture fd added to self.sockets: {future}:{future.connection.fileno()}"
        )

    def _register_future(self, future):
        if isinstance(future, SleepFuture):
            self._register_sleep_future(future)
        elif isinstance(future, DiskIOFuture):
            self._register_disk_io_future(future)
        elif isinstance(future, NetworkIOFuture):
            self._register_network_io_future(future)

    def run_forever(self):
        while True:
            # The event loop first checks all the epoll events which includes socket
            # operations and timer completions
            self._handle_epoll_events()

            # Execute tasks
            # create_task is called on every task to schedule it on the event loop
            # Poll a task from the queue and call the step() function to continue the
            # coroutine's execution
            try:
                task, value = self.runnable_tasks.get_nowait()
            except queue.Empty:
                continue
            future = task.step(value)
            if future:
                print(f"Future being executed: {future}")
                future.waiting_tasks.append(task)

            self._register_future(future)


# The futures reach back into the loop to reschedule their waiting tasks
loop = EventLoop()


# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------


# Timer function
def timer_worker(timer):
    print(f"task{timer}")
    try:
        start = time.perf_counter()
        result = yield SleepFuture(timer)  # Exception handling if the future initialization failed
        stop = time.perf_counter()
        print(f"TimerWorker Complete in time: {stop-start}")
        print(result)
        return 0
    except Exception as e:
        print("Timer Future failed with error: ", e)
        return 1


# DiskIO function
def read_worker():
    print("Reading file")
    try:
        start = time.perf_counter()
        result = yield DiskIOFuture(DISK_IO_FILE)
        stop = time.perf_counter()
        print(f"ReadWorker Complete in time: {stop-start}")
        print(result)
        return 0
    except Exception as e:
        return 1


# Network Function
def network_worker():
    request = (
        f"GET {REQUEST_PATH} HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    try:
        start = time.perf_counter()
        result = yield NetworkIOFuture(request)  # Requires error handling
        stop = time.perf_counter()
        print(f"NetworkWorker Complete in time: {stop-start}")
        print(result)
        # Handle timeout failure such as retries

        return 0
    except Exception as e:
        print(Exception)
        return 1


def main():
    create_pool()

    # Create the tasks and schedule them on the event loop
    loop.create_task(Task(network_worker()))
    loop.create_task(Task(network_worker()))

    # Start the event loop
    loop.run_forever()


if __name__ == "__main__":
    main()
