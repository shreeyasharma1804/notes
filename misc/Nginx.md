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
