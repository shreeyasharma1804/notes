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
