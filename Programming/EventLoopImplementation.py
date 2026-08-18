
"""
Design decisions:
    1. Workers only yeild a future, i.e, a future is the only awaitable object
    2. Client Pool is used by the NetworkFuture
    3. The SSL Connection is non-blocking
"""

from operator import le
import queue
import select
import socket
import time
from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread
from dataclasses import dataclass
import ssl
import os

# Define one epoll instance
epoll = select.epoll()

# Pool definations
MIN_POOL_SIZE = 5       # Should a seperate thread monitor the pool size and create more connections if required
MAX_POOL_SIZE = 10
context = ssl.create_default_context()
pool = Queue()  # Thread safe, q.get() uses semaphores and locks


@dataclass
class ConnectionState:
    """
    TCP and TLS State Definitions
    """

    CONNECTING = 1
    HANDSHAKING = 2
    READY = 3
    ERROR = 4


class SocketWrapper:
    """
    Store socket state
    """

    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        try:
            self.socket.settimeout(2)
            err = self.socket.connect_ex(
                ("httpbin.org", 443)
            )  # Establish TCP layer connectivity
            if err:
                raise Exception
        except Exception as e:
            print(e)
            return

        self.socket = context.wrap_socket(  # TLS Handshake, but not yet
            self.socket, server_hostname="httpbin.org", do_handshake_on_connect=False
        )
        self.state = ConnectionState.CONNECTING
        self.mode = "EPOLLOUT"
        self.timeout_fd = os.timerfd_create(time.CLOCK_REALTIME, flags=os.TFD_NONBLOCK)
        self.readTimeoutStarted = False
        self.writeTimeoutStarted = False


def createPool():
    for _ in range(MAX_POOL_SIZE):
        sock = SocketWrapper()
        pool.put(sock)
    if pool.qsize() < MIN_POOL_SIZE:
        print("Pool Size is less than operational minimum")


class Future(ABC):
    """
    When a task does not immediately yeild the result, and is typically awaited
    """

    @abstractmethod
    def executeWaitingTasks(self):
        pass


class SleepFuture(Future):
    """
        Expects the timer duration from the callee
        The event loop handles the timer expiry, updates the done and result variables,
        and calls executeWaitingTasks, which schedules the tasks waiting on this future back on the runnable queue
    """

    # Executed by worker
    def __init__(self, timer) -> None:
        self.done = False
        self.result = None
        self.waitingTasks = []
        self.timer = timer

    # Executed by Event Loop when the future is complete
    def executeWaitingTasks(self):
        for task in self.waitingTasks:
            loop.createTask(task, self.result)
        self.waitingTasks.clear()


class DiskIOFuture(Future):
    """
    Expects a file_location from the callee
    The event loop creates the thread to offload this disk IO to a thread,
    the thread performs the disk IO, updates the future's done and result variables,
    and calls executeWaitingTasks to schedule the waiting tasks back on the event loop
    """

    # Executed by worker
    def __init__(self, file_location) -> None:
        self.done = False
        self.result = None
        self.file_location = file_location
        self.waitingTasks = []

    # Executed by Event Loop when the future is complete
    def executeWaitingTasks(self):
        for task in self.waitingTasks:
            loop.createTask(task, self.result)
        self.waitingTasks.clear()


class NetworkIOFuture(Future):
    """
    Expects a request from the callee
    The future acquires a non blocking socket from the pool
    When an EPOLLIN or EPOLLOUT event occurs, the event loop reads/writes the data to/from the socket to the future request and response variables
    After recieving the response, the event loop calls executeWaitingTasks to schedule the waiting tasks back on the event loop


    TODO: Healthcheck and keepalive settings at TCP layer
    """

    def __init__(self, request) -> None:
        self.done = False
        self.request = request
        self.response = ""
        self.waitingTasks = []
        self.socket: SocketWrapper = (
            pool.get()
        )  # TODO: Add healthcheck before setting the socket value in the future state
        epoll.register(self.socket.socket.fileno(), select.EPOLLOUT)  # Register a fd and the actions on it which should trigger an event
        self.readTimeout = 10
        self.writeTimeout = 20
        epoll.register(self.socket.timeout_fd, select.EPOLLIN)

    def executeWaitingTasks(self):
        if(self.socket.socket.fileno() != -1):
            print(f"Add {self.socket.socket.fileno()} socket back to pool")
            self.socket.readTimeoutStarted = False
            self.socket.writeTimeoutStarted = False
            pool.put(self.socket)   # Only if socket has not timed-out
            print(pool.__dict__)
        for task in self.waitingTasks:
            loop.createTask(task, self.response)
        self.waitingTasks.clear()


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
            future = self.coroutine.send(
                value
            )  # When a worker hits yeild, it returns the future to send() object. When called again with a value, it 1st sets the result of the future to value and then resumes execution
            return future  # Return future to event loop, so that the event loop schedules its completion
        except StopIteration as e:
            self.result = e.value  # End of execution
        except Exception as e:
            self.exception = e  # Store the exception


class EventLoop:
    def __init__(self) -> None:
        self.runnable_tasks = Queue()
        self.timers = {}
        self.sockets = {}

    def _readFile(self, file_name, future):
        """
        To execute a DiskIO future, the eventloop creates a thread with target as _readFile and starts it.
        The _readFile function reads the file, updates the future and calls
        """
        with open(file_name, "r")  as f:
            contents = f.read()
        print("_readFile thread complete")
        future.done = True
        future.result = contents
        future.executeWaitingTasks()

    def _handleNetworkEventsError(self, future, err):
        future.done = True
        future.socket.state = ConnectionState.ERROR
        future.resposne = err
        future.executeWaitingTasks()

    def _handleNetworkEventTimeout(self, future: NetworkIOFuture):
        if(future.socket.mode == "EPOLLOUT"):
            print(f"WriteTimeout timer started for fd: {future.socket.socket.fileno()} with value: {future}")
            future.socket.writeTimeoutStarted = True
            os.timerfd_settime(
                future.socket.timeout_fd,
                flags=0,
                initial=future.writeTimeout,
                interval=0
            )
        elif(future.socket.mode == "EPOLLIN"):
            print(f"ReadTimeout timer started for fd: {future.socket.socket.fileno()} with value: {future.readTimeout}")
            future.socket.readTimeoutStarted = True
            os.timerfd_settime(
                future.socket.timeout_fd,
                flags=0,
                initial=future.readTimeout,
                interval=0
            )

    def _handleNetworkEvents(self, fd, event):
        future = self.sockets[fd]
        if future.socket.state == ConnectionState.CONNECTING:
            print(f"SSL Handhsake required for socket {future.socket.socket.fileno()}")
            err = future.socket.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err:
                self._handleNetworkEventsError(future, err)
            else:
                future.socket.state = ConnectionState.HANDSHAKING
        if future.socket.state == ConnectionState.HANDSHAKING:
            print(f"Ongoing Handhsake for socket {future.socket.socket.fileno()}")
            try:
                future.socket.socket.do_handshake()  # Continues from the last handshake state
                future.socket.state = ConnectionState.READY
                epoll.modify(fd, select.EPOLLOUT)
            except ssl.SSLWantReadError:  # Handshake requires reading data
                epoll.modify(fd, select.EPOLLIN)
            except ssl.SSLWantWriteError:
                epoll.modify(fd, select.EPOLLOUT)
            except Exception as e:
                self._handleNetworkEventsError(future, e)

        if future.socket.state == ConnectionState.READY:
            print(f"TLS connections exists for socket {future.socket.socket.fileno()}")
            print(f"Current socket mode: {future.socket.mode}")
            if(future.socket.timeout_fd not in self.timers or self.timers[future.socket.timeout_fd] != future):
                self.timers[future.socket.timeout_fd] = future
            if(not future.socket.writeTimeoutStarted):
                self._handleNetworkEventTimeout(future)
            if event & select.EPOLLOUT:  # Socket is writable
                print(f"Ongoing request for socket: {future.socket.socket.fileno()}")
                n = future.socket.socket.send(future.request.encode("utf-8"))
                future.request = future.request[n:]
                if not future.request:  # Stop generating events of the socket being writable once writing the request is complete
                    epoll.modify(future.socket.socket.fileno(), select.EPOLLIN)
                    future.socket.mode = "EPOLLIN"
                    self._handleNetworkEventTimeout(future)
                    print("The socket is now in response mode")
            elif event & select.EPOLLIN:  # Socket is readable
                print(f"Ongoing response for socket: {future.socket.socket.fileno()}")
                data = future.socket.socket.recv(4096)
                data = data.decode("utf-8")
                if not data:  # If EPOLLIN is called with no data, the response is complete. But EPOLLIN keeps getting triggered so this needs to be handled
                    print("Response complete")
                    future.done = True
                    epoll.unregister(future.socket.socket.fileno())
                    future.executeWaitingTasks()
                future.response += data

    def _handleTimerEvents(self, fd):
        future = self.timers[fd]
        os.read(fd, 8)

        if(isinstance(future, SleepFuture)):
            print(f"SleepFuture timer complete: {fd}")
            future.done = True
            future.result = "Timer Complete"
            future.executeWaitingTasks()
            del self.timers[fd]
            epoll.unregister(fd)
            print("Timer unregistered from epoll and event loop")

        elif(isinstance(future, NetworkIOFuture)):
            print(f"Timer expired for future: {future}")
            if(future.socket.mode == "EPOLLOUT"):
                print(f"Request timeout on fd: {future.socket.socket.fileno()}")
                future.result = "Request timeout"
            else:
                print(f"Response timeout on fd: {future.socket.socket.fileno()}")
                future.result = "Response timeout"
            future.done = True

            print(len(self.timers), len(self.sockets))

            del self.timers[fd]    # unregister the timer fd from event loop
            del self.sockets[future.socket.socket.fileno()]    # unregister the socket fd from event loop
            epoll.unregister(fd) # unregister the timer fd from epoll
            epoll.unregister(future.socket.socket.fileno())    # unregister the socket fd from epoll

            print(len(self.timers), len(self.sockets))

            future.socket.socket.close()
            future.executeWaitingTasks()

    def _handleEpollEvents(self):
        """
        Handle read and write events on registered sockets, including non-blocking TLS Handshake events
        When a timer expires on a registered timer_fd, an EPOLLIN event is generated
        """

        events = epoll.poll(0)  # Poll the events on the registered fds

        for fd, event in events:
            # print(fd, self.sockets)
            if fd in self.timers:
                print(f"Epoll timer event: {fd}")
                self._handleTimerEvents(fd)
            elif fd in self.sockets:
                print(f"Epoll network event: {fd}, event: {event}")
                self._handleNetworkEvents(fd, event)
            else:
                continue

    def createTask(self, task, value=None):
        """
        Add a task to the runnable queue
        """
        self.runnable_tasks.put((task, value))

    def executeTask(self):
        while True:
            """
                The event loop first checks all the epoll events which includes socket operations and timer completions
            """
            self._handleEpollEvents()

            # Execute tasks
            """
                createTask is called on every task to schedule it on the event loop
                Poll a task from the queue and call the step() function to continue the coroutine's execution
            """
            try:
                task, value = self.runnable_tasks.get_nowait()
            except queue.Empty:
                continue
            future = task.step(value)
            if future:
                print(f"Future being executed: {future}")
                future.waitingTasks.append(task)

            '''
                If the future is of type SleepFuture, create the timer_fd, call settime on it,
                register with epoll
                and add the timer_fd: future to self.timers
            '''

            if isinstance(future, SleepFuture):
                fd = os.timerfd_create(time.CLOCK_REALTIME, flags=os.TFD_NONBLOCK)
                os.timerfd_settime(
                    fd,
                    flags=0,
                    initial=future.timer,
                    interval=0
                )
                self.timers[fd] = future
                epoll.register(fd, select.EPOLLIN)
                print(f"SleepFuture fd created: {fd}")

            """
                If the future type is of type DiskIOFuture,
                create a thread with _readFile as the target function and start it
                _readFile completes the future and calls executeWaitingTasks
            """

            if isinstance(future, DiskIOFuture):
                file_location = future.file_location
                thread = Thread(
                    target=self._readFile,
                    args=(
                        file_location,
                        future,
                    ),
                )
                thread.start()
                print(f"DiskIOFuture thread created: {thread}")

            '''
                If the Register the socket fd
            '''

            if isinstance(future, NetworkIOFuture):
                self.sockets[future.socket.socket.fileno()] = future
                print(f"NetworkIOFuture fd added to self.sockets: {future}:{future.socket.socket.fileno()}")


createPool()

# Start the loop
loop = EventLoop()

# Timer function
def timerWorker(timer):
    print(f"task{timer}")
    try:
        start = time.perf_counter()
        result = yield SleepFuture(timer)           # Exception handling if the future initialization failed
        stop = time.perf_counter()
        print(f"TimerWorker Complete in time: {stop-start}")
        print(result)
        return 0
    except Exception as e:
        print("Timer Future failed with error: ", e)
        return 1

# DiskIO function
def readWorker():
    print("Reading file")
    try:
        start = time.perf_counter()
        result = yield DiskIOFuture(
            "/home/shreeya/test.txt"
        )
        stop = time.perf_counter()
        print(f"ReadWorker Complete in time: {stop-start}")
        print(result)
        return 0
    except Exception as e:
        return 1

# Network Function
def networkWorker():
    request = (
        "GET /delay/25 HTTP/1.1\r\n"
        "Host: httpbin.org\r\n"
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

# Create the tasks and schedule them on the event loop
# task1 = Task(timerWorker(5))
# task2 = Task(readWorker())
task3 = Task(networkWorker())
task4 = Task(networkWorker())
# loop.createTask(task1)
# loop.createTask(task2)
loop.createTask(task3)
loop.createTask(task4)
# Start the event loop
loop.executeTask()
