### Directory Structure

```bash
┌💁  shreeya @ 💻  pop-os in 📁  nginx
└❯ ls -la
total 84
drwxr-xr-x   8 root root  4096 May 14 22:13 .
drwxr-xr-x 184 root root 12288 May 23 11:06 ..
drwxr-xr-x   2 root root  4096 Apr 23 17:55 conf.d
-rw-r--r--   1 root root  1125 Dec  1  2023 fastcgi.conf
-rw-r--r--   1 root root  1055 Dec  1  2023 fastcgi_params
-rw-r--r--   1 root root  2837 Dec  1  2023 koi-utf
-rw-r--r--   1 root root  2223 Dec  1  2023 koi-win
-rw-r--r--   1 root root  5465 Dec  1  2023 mime.types
drwxr-xr-x   2 root root  4096 Apr 23 17:55 modules-available
drwxr-xr-x   2 root root  4096 Apr 23 17:55 modules-enabled
-rw-r--r--   1 root root  1447 May 14 22:13 nginx.conf
-rw-r--r--   1 root root   180 Dec  1  2023 proxy_params
-rw-r--r--   1 root root   636 Dec  1  2023 scgi_params
drwxr-xr-x   2 root root  4096 May 14 21:51 sites-available
drwxr-xr-x   2 root root  4096 May 14 21:41 sites-enabled
drwxr-xr-x   2 root root  4096 May 14 21:41 snippets
-rw-r--r--   1 root root   664 Dec  1  2023 uwsgi_params
-rw-r--r--   1 root root  3071 Dec  1  2023 win-utf
```

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
