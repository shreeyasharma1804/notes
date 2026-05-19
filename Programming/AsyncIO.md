async: Convert a function to a coroutine

await: Await the results of the called fucntion and yield the control back to the event loop to run other executables

This code would execuete like a synchronous code

```python
import asyncio
import time


async def fetch_data(param):
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    task1 = fetch_data(1)  # Returns a coroutine
    task2 = fetch_data(2)
    result1 = await task1
    print("Task 1 fully completed")
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
print(f"Finished in {t2 - t1:.2f} seconds")
```

Tasks: Unlike coroutines which are scheduled on the event loop only after awaited, tasks are automatically scheduled. Thus, the below code runs asynchronously

```python
import asyncio
import time


async def fetch_data(param):
    print(f"Do something with {param}...")
    await asyncio.sleep(param)
    print(f"Done with {param}")
    return f"Result of {param}"


async def main():
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))
    result1 = await task1
    print("Task 1 fully completed")
    result2 = await task2
    print("Task 2 fully completed")
    return [result1, result2]


t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
print(f"Finished in {t2 - t1:.2f} seconds")
```

Gather coroutines is similar to:

```python
tasks = [
    asyncio.create_task(c)
    for c in coroutines
]

results = []

for task in tasks:
    result = await task
    results.append(result)
```

```python
import asyncio
import time


async def fetch_data(param):
    await asyncio.sleep(param)
    return f"Result of {param}"


async def main():
    # Create Tasks Manually
    task1 = asyncio.create_task(fetch_data(1))
    task2 = asyncio.create_task(fetch_data(2))
    result1 = await task1
    result2 = await task2
    print(f"Task 1 and 2 awaited results: {[result1, result2]}")

    # Gather Coroutines, the coroutines will be scheduled only after await is called on them
    coroutines = [fetch_data(i) for i in range(1, 3)]
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    print(f"Coroutine Results: {results}")

    # Gather Tasks, all the tasks will be scheduled together. If one fails, other tasks continue
    tasks = [asyncio.create_task(fetch_data(i)) for i in range(1, 3)]
    results = await asyncio.gather(*tasks)
    print(f"Task Results: {results}")

    # Task Group, all the tasks will be scheduled together. If one fails, all other tasks are also cancelled
    async with asyncio.TaskGroup() as tg:
        results = [tg.create_task(fetch_data(i)) for i in range(1, 3)]
        # All tasks are awaited when the context manager exits.
    print(f"Task Group Results: {[result.result() for result in results]}")

    return "Main Coroutine Done"


t1 = time.perf_counter()

results = asyncio.run(main())
print(results)

t2 = time.perf_counter()
print(f"Finished in {t2 - t1:.2f} seconds")
```

Run a thread as a coroutine

```python
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor


def fetch_data(param):
    print(f"Do something with {param}...", flush=True)
    time.sleep(param)
    print(f"Done with {param}", flush=True)
    return f"Result of {param}"


async def main():
    # Run in Threads
    task1 = asyncio.create_task(asyncio.to_thread(fetch_data, 1))
    task2 = asyncio.create_task(asyncio.to_thread(fetch_data, 2))
    result1 = await task1
    print("Thread 1 fully completed")
    result2 = await task2
    print("Thread 2 fully completed")
```

Run processes from a process executor pool in the event loop:


```python
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor


def fetch_data(param):
    print(f"Do something with {param}...", flush=True)
    time.sleep(param)
    print(f"Done with {param}", flush=True)
    return f"Result of {param}"


async def main():

    loop = asyncio.get_running_loop()

    with ProcessPoolExecutor() as executor:
        task1 = loop.run_in_executor(executor, fetch_data, 30)
        task2 = loop.run_in_executor(executor, fetch_data, 60)

        result1 = await task1
        print("Process 1 fully completed")
        result2 = await task2
        print("Process 2 fully completed")

    return [result1, result2]


if __name__ == "__main__":
    t1 = time.perf_counter()

    results = asyncio.run(main())
    print(results)

    t2 = time.perf_counter()
    print(f"Finished in {t2 - t1:.2f} seconds")
```

- Every function declared with async is a coroutine, i.e. it becomes schedulable on the event loop
- await places the coroutine in the waiting queue.
- Actions which can be run on the event loop are essentially in different queues like runnable, waiting etc.
- Timers: Create a thread which runs the native sleep function. Update the future when the timer completes
- Read a file: Create a seperate thread which can read the file. Once the reading is complete, the thread updates the future. Coroutines subscribe to a future. future.set_result() notifies all the threads which is then placed in the runnable queue.
- Networking: Similar to epoll like design.
- to_thread: Threads subsribe to futures which notify the event loop.
- A return inside a coroutine ends that coroutine's execution immediately
