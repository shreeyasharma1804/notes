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

### Atomic Synchronization

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
```

### False sharing 

- Locking a cache line can introduce false sharing between 2 threads updating different variables but on the same cache line

```go
package main

import (
	"sync"
	"sync/atomic"
)

type Counter struct {
	count1 atomic.Int64
	_      [56]byte
	count2 atomic.Int64
}

func incrementSharedState(s *Counter, wg *sync.WaitGroup, id int) {
	defer wg.Done()
	for j := 0; j < 1000000; j++ {
		if id == 0 {
			s.count1.Add(1)
		} else {
			s.count2.Add(1)
		}
	}
}

func main() {
	// var myCounter atomic.Uint64
	// myCounter.Add(1)
	// fmt.Println(myCounter.Load())

	c := Counter{}

	var wg1 sync.WaitGroup
	wg1.Add(1)
	var wg2 sync.WaitGroup
	wg2.Add(1)
	go incrementSharedState(&c, &wg1, 0)
	go incrementSharedState(&c, &wg2, 1)
	wg1.Wait()
	wg2.Wait()

}
```
Without and with false sharing

```bash
concurrency ⟩ time ./concurrency                                                                                                                 ~/D/g/concurrency

________________________________________________________
Executed in   15.24 millis    fish           external
   usr time   14.33 millis    0.31 millis   14.02 millis
   sys time    5.29 millis    1.38 millis    3.91 millis


concurrency ⟩ go build -o concurrency .                                                                                                          ~/D/g/concurrency

concurrency ⟩ time ./concurrency                                                                                                                 ~/D/g/concurrency

________________________________________________________
Executed in  857.11 millis    fish           external
   usr time   29.26 millis    0.25 millis   29.01 millis
   sys time    6.10 millis    1.16 millis    4.94 millis
```

### Mutexes

```go
c.mu.Lock()
defer c.mu.Unlock()
c.counters[name]++
```

- Mutexes and semaphores also use lock inc instruction to atomically increment and decrement a shared variable which acts as a software level lock
- A goroutine waiting on a lock is eventually put on waiting queue
- Unlock() wakes up one process from the queue
