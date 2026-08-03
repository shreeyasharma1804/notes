## Async Programming

- async: Convert the function to a coroutine
- await: Yield the control back to the event loop

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
