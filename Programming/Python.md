## Async Programming

- async: Convert the function to a coroutine, i.e it becomes schedulable on the event loop
- await: Await a task, and then yield the control back to the event loop

```python
import asyncio
import time

async def foo(seconds):
    await asyncio.sleep(seconds)
    return "Timer Completed"
    
async def main():
    coroutine1 = foo(5)      # This returns a coroutine object
    coroutine2 = foo(5)
    
    # Coroutine object needs to be awaited in ordert o schedule them on the event loop
    
    await coroutine1         # Wait till coroutine1 is complete
    await coroutine2         # Wait till coroutine2 is complete
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1)    # Takes 10 seconds because this code runs synchronously
```

### create_task

- tasks and coroutines are different objects

```python
import asyncio
import time

async def foo(seconds):
    await asyncio.sleep(seconds)
    return "Timer Completed"
    
async def main():
    task1 = asyncio.create_task(foo(5))   # Schedule the task on the event loop and return a task object   
    task2 = asyncio.create_task(foo(5))
    
    result = await task1                  # Wait till task1 is complete
    await task2                           # Wait till task2 is complete
    
    print(result)
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1)    # Since both the coroutines are scheduled on the event loop, this program takes 5 seconds to execute
```

### Gather coroutines (await multiple coroutines together)

```python
import asyncio
import time

async def foo(seconds):
    await asyncio.sleep(seconds)
    return "Timer Completed"
    
async def main():
    coroutines = [foo(5) for i in range(5)]
    result = await asyncio.gather(*coroutines, return_exceptions = True) # Schedule all the coroutines on the event loop together and await them, might be using create_task internally
    print(result[0]) # Prints "Timer Completed"
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1) # 5 seconds
```

### Gather tasks (await multiple tasks together)

- If one task fails, other tasks continue

```python
import asyncio
import time

async def foo(seconds):
    await asyncio.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    tasks = [asyncio.create_task(foo(5)) for i in range(5)]
    result = await asyncio.gather(*tasks, return_exceptions=True)
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1) # 5 seconds
```

- Any await-able object(coroutine, task, future) is compatible to be run inside asyncio.gather 

### Task Groups

- Schedule tasks using task groups
- The tasks are automatically awaited
- If one task fails, the other tasks also fail. Use task groups when this feature is a requirement

```python
import asyncio
import time

async def foo(seconds):
    await asyncio.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    async with asyncio.TaskGroup() as tg:
        results = [tg.create_task(foo(5)) for i in range(5)]
        print(results)        # Prints the created task objects which are in pending state
    print(results)    # Prints the task object along with the values returned by the function executed by the task
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()

print(t2-t1)      # 5 seconds
```

### to_thread

- Used to offload synchronous code to a thread and then await it using create_task

```python
import asyncio
import time

def foo(seconds):
    time.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    task1 = asyncio.create_task(asyncio.to_thread(foo, 5))
    task2 = asyncio.create_task(asyncio.to_thread(foo, 5))
    
    await task1
    await task2
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1)      # 5 seconds
```

### Using thread pool executor

- Offload synchronous tasks to a thread from a thread pool

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Create 8 idle threads
executor = ThreadPoolExecutor(max_workers=5)

# Synchronous function
def foo(seconds):
    time.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    loop = asyncio.get_running_loop()    # Get the event loop
    
    futures = [loop.run_in_executor(executor, foo, 5) for i in range(5)]     # Offload the synchronous process to a thread from the thread pool, which is awaited by the event loop
    await asyncio.gather(*futures)
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1)      # 5 seconds
```

```python
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

# Create 8 idle threads
executor = ThreadPoolExecutor(max_workers=2)

# Synchronous function
def foo(seconds):
    time.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    loop = asyncio.get_running_loop()    # Get the event loop
    
    futures = [loop.run_in_executor(executor, foo, 5) for i in range(5)]     # Offload the synchronous process to a thread from the thread pool, which is awaited by the event loop
    await asyncio.gather(*futures)
    
t1 = time.perf_counter()
asyncio.run(main())          # Start the event loop
t2 = time.perf_counter()


print(t2-t1)      # 15 seconds (2 threads in parallel + 2 threads in parallel + 1 last execution)
```

### Using ProcessPoolExecutor

- Offload to processes, useful for multicore systems the code is doing CPU intensive operations and GIL could be a limitation

```python
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor

# Synchronous function
def foo(seconds):
    time.sleep(seconds)
    return "Timer Completed"
    
async def main():
    
    loop = asyncio.get_running_loop()    # Get the event loop
    
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [loop.run_in_executor(executor, foo, 5) for i in range(5)]
        await asyncio.gather(*futures)
    
if __name__ == "__main__":
    t1 = time.perf_counter()

    asyncio.run(main())

    t2 = time.perf_counter()
    print(f"Elapsed: {t2 - t1:.2f} seconds")
```

## Threading

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

In Python, by default, threads are non-daemon. Python's main thread will not exit until all non-daemon threads have finished, regardless of  `join()` called or not.

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

### Race Conditions

- If multiple threads access a common variable, race conditions occur.
- Writes are lost due to dirty reads

```python
import threading
import time

shared_state = 0

def foo():
    global shared_state
    for i in range(1000000):
        shared_state += 1
        
    
t1 = threading.Thread(target=foo)
t2 = threading.Thread(target=foo)

t1.start()
t2.start()

start = time.perf_counter()

t1.join()
t2.join()

stop = time.perf_counter()

print(stop-start)

```

### Debugging

Print the thread id:

```python
print(threading.get_native_id())
```

#### py-spy

```bash
py-spy dump --pid <pid>      # Shows the processes with high CPU usage
py-spy dump --native --locals --pid <pid>  # If a function is at the same code after multiple dumps, it indicates lock contention deadlock etc
py-spy record -o profile.json --format speedscope --pid <pid>  # Shows the call trace and the amount of CPU time
```

#### scalene

```
scalene run <python file>   # Scalene profiles the code line by line to show the exact time the line ran for during the profiling and the memory used by it
```

### Decoraters

Middlewares can be implemented using decoraters

```python
import time

def timer(func):
    def wrapper():
        start = time.time()
        func()
        end = time.time()
        print(f"Took {end-start:.2f}s")

    return wrapper


@timer
def work():
    time.sleep(2)

work()
```

### Callbacks

A callback is a function passed as an argument to another function to be called later

```python
def greet():
    print("Hello")

def execute(callback):
    print("Starting...")
    callback()
    print("Done")

execute(greet)
```
