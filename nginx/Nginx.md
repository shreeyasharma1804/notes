| Component                     | Your Server | Nginx         |
| ----------------------------- | ----------- | ------------- |
| Multi-worker                  | Yes         | Yes           |
| fork() workers                | Yes         | Yes           |
| epoll                         | Yes         | Yes           |
| nonblocking sockets           | Yes         | Yes           |
| event-driven                  | Yes         | Yes           |
| thread-per-connection avoided | Yes         | Yes           |
| reverse proxy logic           | No          | Yes           |
| async state machines          | Minimal     | Extensive     |
| HTTP engine                   | No          | Advanced      |
| upstream handling             | No          | Yes           |
| timers                        | No          | Yes           |
| buffering                     | Minimal     | Sophisticated |
| graceful reload               | No          | Yes           |

### Sendfile

```
# Turn of sendfile
sendfile off

# Turn on sendfile
sendfile on

# This makes serving large files faster
```

### kTLS

- Nginx uses openssl for TLS.
- To check if nginx is using kTLS:
    - Check: `cat /proc/net/tls_stat`


```
ps aux | grep nginx
sudo strace -f -e trace=setsockopt -p <worker_pid>
setsockopt(45, SOL_TLS, TLS_TX, ...) # If kTLS is enabled
```
