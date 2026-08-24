eBPF programs attach to a tracepoint

A tracepoint can be compared to tracing in opentelemetry

List all available tracepoints:

sudo ls /sys/kernel/debug/tracing/events/syscalls/

```c
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

# The tracepoint which will execute the handle_write function
SEC("tracepoint/syscalls/sys_enter_write")

int handle_write(void* ctx) {
    bpf_printk("write() system call was called\n");
    return 0;

}

char LICENSE[] SEC("license") = "GPL";
```

Generate the user facing APIs

```
bpftool gen skeleton hello.bpf.o > hello.skel.h
```

```
#include <stdio.h>
#include <unistd.h>

#include "hello.skel.h"

int main()
{
    struct hello_bpf *skel;

    skel = hello_bpf__open_and_load();
    if (!skel) {
        fprintf(stderr, "Failed to open/load BPF program\n");
        return 1;
    }

    # Atatch the bpf program to the system call
    if (hello_bpf__attach(skel)) {
        fprintf(stderr, "Failed to attach BPF program\n");
        hello_bpf__destroy(skel);
        return 1;
    }

    printf("BPF program attached.\n");
    printf("Run some commands in another terminal.\n");

    while (1) {
        sleep(1);
    }

    hello_bpf__destroy(skel);

    return 0;
}
```

The pipe where the logs are printed: sudo cat /sys/kernel/debug/tracing/trace_pipe
