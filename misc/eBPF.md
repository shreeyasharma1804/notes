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


### Arrays

```
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <stddef.h>

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, __u64);
} sys_call_counter SEC(".maps");


SEC("tracepoint/syscalls/sys_enter_read")
int count_writes(void* ctx)
{
    __u32 key = 0;

    __u64 *value =
        bpf_map_lookup_elem(&sys_call_counter, &key);

    if (value) {
        (*value)++;

        bpf_printk(
            "write() system call was called %llu times\n",
            (unsigned long long)*value
        );


        bpf_printk("FD: %d", ctx->fd);

    }

    return 0;
}


SEC("tracepoint/sched/sched_process_exec")
int count_execs(void *ctx)
{
    bpf_printk("exec() system call was called");
    return 0;
}


char LICENSE[] SEC("license") = "GPL";
```
