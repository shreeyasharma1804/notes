### General

- In C, declared variables initially hold a garbage value, i.e, they are not 0 initialized
- Both implicit and explicit casting is supported

### Void Pointers

- Use when the type of the data/pointer is not relevant
- Type casting is required

```c
#include <stdio.h>

void foo(void* arg) {
    printf("%d", *(int*)arg);
}

int main() {
    int x = 10;
    int* y = &x;
    *y = 0xDEADBEEF;
    foo(y);
}
```

### Const pointers

```c
int main() {

    // Both declarations are equivalent
    const int x = 8;
    int const y = 10;
    int z = 30;
    
    // Pointer to type const int, used to ensure that the address the pointer points can not be dereferenced to a new value
    
    const int* px = &x;
    px = &y;             // Works
    // *px = 20;            // Does not work

    // Const pointer to type int
    // Pointer cannot point to a different address but 
    // dereferencing can change the value
    
    int* const py = &y;
    // py = &x; Does not work

    *py = 20;  // Works

    // const pointer to type const int

    const int* const pz = &z;
    
    return 0;
}
```
