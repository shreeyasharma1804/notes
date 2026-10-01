### General

- Declared variables are 0 initialized, this is slower but provides safer code
- Typed variable declaration

```go
var x int;
```

- Untyped variable declaration

```go
x := 10
```

- Explicit casting is supported
- Implicit casting is only supported for untyped variables


### Static vs Dynamic memory allocation

- Unlike C, where variables with defined sizes are allocated on the stack, whereas malloc explicitly allocates memory on the heap, go uses escape analysis
- Variables with dynamic sizes like slices can be allocated on the stack if the do not escape their scope
- Memory allocation tools like make and new also use brk and mmap like mechanisms to get more memory

#### make

- Only initialize slices, maps etc
- The memory is memset to 0
- The capacity defines how much initial memory to allocate

#### Atomic Synchronization

- For synchronization, the cache line is locked and the increment is done using one instruction

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func incrementSharedState(i *atomic.Int64, wg *sync.WaitGroup) {
	defer wg.Done()
	for j := 0; j < 1000000; j++ {
		i.Add(1)                 // Equivalent to lock inc qword [counter]
	}
}

func main() {
	// var myCounter atomic.Uint64
	// myCounter.Add(1)
	// fmt.Println(myCounter.Load())

	var i atomic.Int64
	var wg1 sync.WaitGroup
	wg1.Add(1)
	var wg2 sync.WaitGroup
	wg2.Add(1)
	go incrementSharedState(&i, &wg1)
	go incrementSharedState(&i, &wg2)
	wg1.Wait()
	wg2.Wait()
	fmt.Println(i.Load())

}
⁄```
