### State Management

- Traditionally, states are managed through objects

```js

// Equivalent to useState()

class useState {
    constructor(count){
        this.count = count;
    }

    setCount(callback) {
        this.count = callback(this.count);
    }
}

let count = new useState(0); 

count.setCount((c) => c+1)

console.log(count.count);
```

- To manage states through functions, closures are used
- Closures allow to access a variable defined in an outer function even after the outer function has exited

```js
function useState(count) {
    let internalCount = count;

    function getCount() {
        return internalCount;
    }

    function setCount(callback) {
        internalCount = callback(internalCount);
    }

    return [getCount(), setCount]
}

[getCount,setCount] = useState(0);
// console.log(getCount());

setCount(c => c+1);
console.log(getCount);
```

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
    await asyncio.sleep(1)
    callback()

async def main():
    await returns_promise(callback)

asyncio.run(main())
```

- Named vs nameless exports
