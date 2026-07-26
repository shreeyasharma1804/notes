- Promises

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
