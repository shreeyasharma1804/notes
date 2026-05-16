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
