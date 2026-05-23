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

```bash
# nginx.conf

user www-data;                      # nginx.conf worker processes run as www-data user
worker_processes auto;              # Number of worker processes is equa to the number of CPU cores
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;
include /etc/nginx/modules-enabled/*.conf;

events {
	worker_connections 768;         # The maximumum number of processes a worker process can handle
	# multi_accept on;
}

http {

	##
	# Basic Settings
	##

	sendfile off;
	tcp_nopush on;                           # TCP Buffering, wait and send larger packets 
	types_hash_max_size 2048;                # Hashmap size of the mime type hashtable

	include /etc/nginx/mime.types;           # If nginx has to serve the files manually, the content-type is fetched from the mime type
	default_type application/octet-stream;   # Default content-type

	##
	# SSL Settings
	##

	ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE 
	ssl_prefer_server_ciphers on;            # The server chooses the cipher type

	##
	# Logging Settings
	##

	access_log /var/log/nginx/access.log;

	##
	# Gzip Settings
	##

	gzip on;

	# gzip_vary on;
	# gzip_proxied any;
	# gzip_comp_level 6;
	# gzip_buffers 16 8k;
	# gzip_http_version 1.1;
	# gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

	##
	# Virtual Host Configs
	##

	include /etc/nginx/conf.d/*.conf; 
	include /etc/nginx/sites-enabled/*;       # All files in sites-enabled are simlinks to sites-available
}
```

### Commands

nginx -s signal

-  `stop` — fast shutdown
-  `quit` — graceful shutdown
-  `reload` — reloading the configuration file
-  `reopen` — reopening the log files


### Load Balancing

```nginx
http {

    upstream app_backend {
		zone backend 64k;
        server 10.0.0.11:8080 weight 3 max_conn 10;
        server 10.0.0.12:8080;
        server 10.0.0.13:8080;
		queue 100 timeout 30;
		keepalive 32;
    }

    server {
        listen 80;
        server_name example.com;                                             # This block executes only if the host sent by the client is equal to server_name

        location / {
            proxy_pass http://app_backend;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;                         # remote_addr contains the client that directly connected to nginx
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;     # Add $remote_addr to the X-Forwarded-For list
            proxy_set_header X-Forwarded-Proto $scheme;
			proxy_connect_timeout: 30s;										 # Upstream connect timeout                                       
        }
    }
}
```

- `max_conns` in an upstream server tells Nginx the maximum number of **active upstream requests** it should allow to a backend at a time. An active connection means a request has been assigned to that backend and is still in progress (Nginx is waiting for the upstream response to complete); idle keepalive connections do not count. When a client request arrives, Nginx accepts it (`accept`), reads and parses the HTTP request, selects an upstream server, and checks whether that server's active connection count is below `max_conns`. If capacity exists, Nginx creates or reuses an upstream socket and forwards the request. If all backend servers have reached their `max_conns` limit, Nginx does **not** try to connect and then fail at the socket level; instead it places the already-parsed request into the configured upstream `queue`, which is an in-memory Nginx queue of waiting HTTP requests. Requests stay there until an active upstream request finishes (at which point the active count decreases), or until the queue timeout expires, in which case Nginx typically returns `503 Service Unavailable`.
- timeout: a request in the queue can wait for 30 seconds before it timesout and a 503 response code is sent
- keepalive: The maximum number or idle connections one worker can keep cached to all the upstream servers combined.
- Loadbalancing algorithms used are round robin, ip hashin (sticky sessions) etc.
- If a client closes a connection due to timeout where the response was not sent, the recv() call returns 0 and nginx silently writes 499 to the logs.
- zone: Ceates a 64 KB shared memory area named backend that all Nginx worker processes can access to store and synchronize upstream state. Since Nginx workers are separate processes with separate memory, without a zone each worker would maintain its own independent view of backend information such as active connection counts, failures, and load-balancing state, which could make features like max_conns inaccurate across workers.
- default: Multiple domains might route to the same IP, thus the same nginx server. Each server block handles one host. The server block defined with default executes if no host matches

### Routing

- Strict match:

`location = /login`: Matches only /login and not /login/*
`location = /login/`: Matches only /login/ and not /login

- ~: Case sensitive regex matching
- ~*: Case insensitive regex matching

The evaluation order is:

1. Check exact matches (=)
2. Find longest prefix (All paths that do not start with ~)
3. Check ^~ rule (Used in prefix mathcing, if the prefix matches, stop here, if not, any matching regex can override)
4. Check regexes in order (The order of the location block matters, the 1st match is selected)
5. Fall back to prefix


- Difference in /login and /login/

```
/login:

/login
/login/
/login/user
/login123
/loginABC

/login/ would only match:

/login/
/login/user
/login/profile/edit
```

### Client timeouts

```nginx
server {
    client_header_timeout 10s;
    client_body_timeout 30s;           # For POST requests
    keepalive_timeout 65s;
    send_timeout 30s;                  # Client socket not writable
}
```

HTTP Code: 408 request timeout

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

## Optimizations

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
