### Promises

```js
function returnsPromise() {
    return new Promise((resolve, reject) => {
        try {
            setTimeout(()=>{console.log("Hi")}, 1000);
            resolve("Resolved");
        }
        catch {
            reject("Rejected");
        }
    })
}

returnsPromise().then(() => {console.log("Promise 1 complete")});
returnsPromise().then(() => {console.log("Promise 2 complete")});
```

Python equivalent

```python
import asyncio

def callback():
    print("Promise completed")

async def returns_promise(callback):
    await asyncio.sleep(1)   # seconds, not milliseconds
    callback()

async def main():
    await returns_promise(callback)

asyncio.run(main())
```
