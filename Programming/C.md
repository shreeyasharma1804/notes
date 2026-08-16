### Void Pointers

- Use when the type of the data/pointer is not relevant
- De referencing is required

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
