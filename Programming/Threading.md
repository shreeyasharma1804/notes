Concurrency: Achieved via context switching

Parallelism: Achieved via multiple cores

### Create and Join Threads

```python
import threading
import time

def  func1():
	for  i  in  range(10):
		time.sleep(1)
		print("Hi func1",  i)

def  func2():
	for  i  in  range(10):
		time.sleep(2)
		print("Hi func2",  i)

# Create the thread
t1  = threading.Thread(target=func1)
t2  = threading.Thread(target=func2)

# Start the thread
t1.start()
t2.start()

# Process completed only after both t1 and t2 are complete
```

In C, a posix thread which is not waited on, (by `join`), will be killed once the main process exits

In Python, by default, threads are non-daemon
Python's main thread will not exit until all non-daemon threads have finished, regardless of  `join()` called or not.

```python
t1  = threading.Thread(target=func1,  daemon=True)
t2  = threading.Thread(target=func2,  daemon=True)
```

If join is not called on either of the threads, the main process exits immediately and no thread is executed

```python
t1  = threading.Thread(target=func1,  daemon=True)
t2  = threading.Thread(target=func2,  daemon=True)

t1.start()
t2.start()

t1.join() 
# The process exits immediately after t1 is complete, does not wait for t2
``` 

### Pass arguments

To pass an argument:

```python
t1  = threading.Thread(target=func1,  args=("Hi func1",),  daemon=True)
```

There is no mechanism to get the return value from the thread, so mutable global variables are used.

Example:

```python
result =  [None]
def  func1(result):
	result[0] = "Hello from func1"
```

### Race conditions

```python
import threading
import time

counter  =  0

def  func1():
	for  i  in  range(100000000):
		global  counter
		counter  +=  1

t1  = threading.Thread(target=func)
t2  = threading.Thread(target=func)

t1.start()
t2.start()

t1.join()
t2.join()

print(counter)
```

Without threading:

```bash
200000000

________________________________________________________
Executed in    5.83 secs    fish           external
   usr time    5.77 secs    0.27 millis    5.77 secs
   sys time    0.03 secs    1.25 millis    0.03 secs
```

With threading:

```bash
135069571

________________________________________________________
Executed in    5.28 secs    fish           external
   usr time    5.19 secs    0.27 millis    5.19 secs
   sys time    0.04 secs    1.35 millis    0.04 secs
```

- The program execution has higher kernel time with threading
- The returned value was incorrect (The add operations are lost due to dirty reads)


Race conditions are avoided using locks

### Mutexes

```python
import threading
import time

lock  = threading.Lock()
counter  =  0

def  func1():
	global  counter
	for  i  in  range(100000000):
		with  lock:
			counter  +=  1 

t1  = threading.Thread(target=func)
t2  = threading.Thread(target=func)

t1.start()
t2.start()

t1.join()
t2.join()
 
print(counter)
```

```bash
200000000

________________________________________________________
Executed in   21.19 secs    fish           external
   usr time   21.01 secs    0.27 millis   21.01 secs
   sys time    0.13 secs    1.32 millis    0.13 secs
```

The execution time is higher than a single threaded process because of locking.

Execution time analysis:

Task: Count to 200000000

| Number of threads | Execution time |
|-----------------------| ------------|
| 2 | 0.13 |
| 4 | 0.25 |
| 8 | 1.93 |
| 16 | 94.18

- Execution time increases exponentially when threads are used with mutexes.
- Thus, usage of threads should be avoided when possible if memory sharing is involved since the overall performance decreases compared to a single threaded operation

### Binary Semaphores

```python
# 1:1 Read write syncronization using binary semaphores

# semaphore.acquire() => wait => wait till the value > 0 and then decrement by 1

# semaphore.release() => post => increment by 1

import threading
import time

read_semaphore  = threading.Semaphore(0)
write_semaphore  = threading.Semaphore(1)

counter  =  0
list  =  []

def  reader():
	while  True:
		global  counter
		read_semaphore.acquire()
		print(list[counter])
		counter  +=  1
		time.sleep(1)
		write_semaphore.release()

def  writer():
	while  True:
		write_semaphore.acquire()
		list.append(counter)
		time.sleep(1)
		read_semaphore.release()

t1  = threading.Thread(target=reader)
t2  = threading.Thread(target=writer)

t1.start()
t2.start()
```

In this example, 2 threads are coordinating reads and writes using 2 binary semaphores

#### Reader-Writer lock

The performance of mutexes and reader-writer locks degrades equally as the number of threads increase

```python
import threading

        # ---------------------------------------------------------------------------
        # |    Think of a condition as a wait queue of sleeping threads              |
        # |                                                                          | 
        # |    When a thread calls self.condition.wait(),                            | 
        # |     it is put to sleep state and added to the wait queue                 | 
        # |                                                                          |
        # |    When a thread calls self.condition.notify_all(),                      |
        # |    all sleeping threads wake up and check the while loop                 |
        # |                                                                          |
        # |    Waking up multiple writers together in this case is fine because,     |
        # |    the threads need to acquire self.lock again                           |
        # |    Note: notify()  wakes up one thread from the wait queue               |	  
        # ---------------------------------------------------------------------------- 

class ReaderWriter:

    def __init__(self) -> None:
        self.readers = 0
        self.writers = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock) # If a thread is sleeping on self.condition, self.lock is unlocked

    def acquireReader(self):
        with self.lock:
            while(self.writers != 0):
                self.condition.wait()
            self.readers += 1

    def releaseReader(self):
        with self.lock:
            self.readers -= 1

            if(self.readers == 0):
                self.condition.notify_all()

    def acquireWriter(self):
        with self.lock:
            while(self.readers > 0 or self.writers > 0):
                self.condition.wait()
            self.writers += 1

    def releaseWriter(self):
        with self.lock:
            self.writers -= 1

            if(self.writers == 0):
                self.condition.notify_all()
```

### Thread local storage

- Each thread gets its own instance of a variable
- For intuition: hashmap: `threading.get_native_id(): thread_value`

```python
import threading

# Create a thread-local storage object
local_data = threading.local()

def thread_func(value):
    local_data.number = value  # Each thread sets its own copy
    print(f"Thread {threading.current_thread().name}: local_data.number = {local_data.number}")

t1 = threading.Thread(target=thread_func, args=(10,), name="T1")
t2 = threading.Thread(target=thread_func, args=(20,), name="T2")

t1.start(); t2.start()
t1.join();  t2.join()
```

### Multi-threaded performance
- Multi-threaded functions may perform slower due to shared memory read and writes (locks)
- False sharing, if 2 threads are working on 2 variables which fall in the same cache line, in that case, there will be frequent l1 cache misses. To avoid this, use padding between the variable definitions. Example, in `counter = [0,0]`, this may end up on the same cache line
- Pure Python threads can never be truly parallel due to the GIL (ensures that only one python thread is executing at a single time, even with multiple cores).
- Excessive threads cause a further slow down due to context switch overhead
- Optimal number of threads: `ThreadPoolExecutor`'s default formula `min(32, cpu_count + 4)` is a reasonable starting point for most I/O bound workloads.

### Multiprocessing

```python
from multiprocessing import Process
import os

def worker(name):
    print(f"{name} running on PID {os.getpid()}")

p1 = Process(target=worker, args=("P1",))
p2 = Process(target=worker, args=("P2",))

p1.start(); p2.start()
p1.join(); p2.join()
```

- With CPU core affinity

```python
import psutil
import os
from multiprocessing import Process

def worker(name, core_id):
    process = psutil.Process(os.getpid())
    process.cpu_affinity([core_id])   # pin to specific core
    print(f"{name} pinned to core {core_id}, PID {os.getpid()}")
    # do work...

p1 = Process(target=worker, args=("P1", 0))  # pinned to core 0
p2 = Process(target=worker, args=("P2", 1))  # pinned to core 1

p1.start(); p2.start()
p1.join(); p2.join()
```

### More details

- Traditional locking systemcall require the CPU to switch into kernel mode to acquire a lock
- Modern locks use futex, which acquire the lock in the user space
- Switch to kernel space is only required if the kernel has to put a thread to sleep when a lock is already acquired.
- If a thread tries to acquire a lock which is already held, it goes to sleep and placed in a waiting queue by the kernel (similar to the wait and notify mechanism in rw lock)

### Debugging

Print the thread id:

```python
print(threading.get_native_id())
```

```bash
py-spy dump --pid <pid>      # Shows the processes with high CPU usage
py-spy dump --native --locals --pid <pid>  # If a function is at the same code after multiple dumps, it indicates lock contention deadlock etc
py-spy record -o profile.json --format speedscope --pid <pid>  # Shows the call trace and the amount of CPU time
```
