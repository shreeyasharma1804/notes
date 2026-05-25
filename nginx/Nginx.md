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
	worker_connections 768;         # The maximumum number of client connections a worker process can handle
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

- Trailing / difference in proxy pass for /api:

| Config                           |     Request | Sent upstream |
| -------------------------------- | ----------: | ------------: |
| `proxy_pass http://backend;`     | `/api/test` |   `/api/test` |
| `proxy_pass http://backend/;`    | `/api/test` |       `/test` |
| `proxy_pass http://backend/v1/;` | `/api/test` |    `/v1/test` |


### SSL

To enable SSL:

```nginx
listen 443 ssl;
```

SSL Termination:

```nginx
server {
	listen  4000  ssl;
	ssl_certificate /etc/nginx/certificate.crt;
	ssl_certificate_key /etc/nginx/private.key;
	location / {
		proxy_pass  http://backend/;     # Notice http and not https
	}
}
```

mTLS (Client to nginx)

```nginx
server {
    listen 443 ssl;

    # Server identity
    ssl_certificate     /etc/nginx/server.crt;
    ssl_certificate_key /etc/nginx/server.key;

    # Trusted CA for client certificates
    ssl_client_certificate /etc/nginx/client-ca.crt;

    # Require client certificate
    ssl_verify_client on;

    location / {
        proxy_pass http://backend;

        proxy_set_header X-Client-Verify $ssl_client_verify;        # Certificate verification output
        proxy_set_header X-Client-DN $ssl_client_s_dn;              # Client certificate subject
    }
}
```

SSL Bridge

```nginx
server {
    listen 443 ssl;

    ssl_certificate /etc/nginx/server.crt;
    ssl_certificate_key /etc/nginx/server.key;

    location / {
        proxy_pass https://backend;

        proxy_ssl_verify on;
        proxy_ssl_trusted_certificate /etc/nginx/backend-ca.crt;
    }
}
```

mTLS (nginx to upstream )

```nginx
    proxy_ssl_certificate     /etc/nginx/nginx-client.crt;
    proxy_ssl_certificate_key /etc/nginx/nginx-client.key;
```

Caching

Store the session ids for faster tls handshake

```nginx
ssl_session_cache   shared:SSL:10m; 10MB cache size
ssl_session_timeout 10m;
```

### Timeouts


```nginx
server {
    client_header_timeout 10s;         # Maximum time to get client headers
    client_body_timeout 30s;           # For POST requests
    keepalive_timeout 65s;             
    send_timeout 30s;                  # Client socket not writable
`	keepalive_requests 1000;           # Maximum number of requests that can be sent on one connection


	location / {
		proxy_connect_timeout 5s;      # Maximum time to establish connection with upstream server
		proxy_send_timeout 30s;        # Maximum time to write to upstream server socket (i.e. Time to send request to upstream)
		proxy_read_timeout 60s;        # Maximum time to read the upstream server socket (i.e. Time to revieve response from upstream)
	}
}
```

### Buffering

Request buffering:

```nginx
client_header_buffer_size 1k;
large_client_header_buffers 4 8k;      # Large headers spill across 4 units of extra 8kB storage, used to avpid 400 response code due to huge cookies

client_body_buffer_size 8k;
client_body_temp_path                  # If the client body size exceeds, it is stored in this temp location

proxy_request_buffering on;            # Enable buffering
proxy_request_buffering off;           # Enable Streaming
```

Resposne buffering

```nginx
proxy_buffer_size 2k;                  
proxy_buffers 16 4k;                   #  Large responses spill across 16 units of extra 4kB storage
```

### WAF

### Rate Limiting

### Health Checks

### HTTP codes

| HTTP Code                                      |                                    Typical NGINX Condition | Relevant Directive(s)                                               |
| ---------------------------------------------- | ---------------------------------------------------------: | ------------------------------------------------------------------- |
| `301 Moved Permanently`                        |                                         Permanent redirect | `return 301`, `rewrite`                                             |
| `302 Found`                                    |                                         Temporary redirect | `return 302`, `rewrite`                                             |
| `400 Bad Request`                              | Malformed request, invalid headers, invalid request syntax | `ignore_invalid_headers`, `large_client_header_buffers`             |
| `401 Unauthorized`                             |                                    Authentication required | `auth_basic`, `auth_basic_user_file`                                |
| `403 Forbidden`                                |                                              Access denied | `deny`, `allow`, `limit_except`, `autoindex`                        |
| `404 Not Found`                                |                            Requested file/resource missing | `root`, `alias`, `try_files`                                        |
| `405 Method Not Allowed`                       |                                     Request method blocked | `limit_except`                                                      |
| `408 Request Timeout`                          |                            Client too slow sending request | `client_header_timeout`, `client_body_timeout`                      |
| `413 Payload Too Large`                        |                                 Request body exceeds limit | `client_max_body_size`                                              |
| `414 URI Too Long`                             |                                 Request URI exceeds limits | `large_client_header_buffers`                                       |
| `431 Request Header Fields Too Large`          |                                  Request headers too large | `large_client_header_buffers`                                       |
| `429 Too Many Requests`                        |           Rate limit exceeded *(if configured explicitly)* | `limit_req`, `limit_req_zone`                                       |
| `500 Internal Server Error`                    |                              Internal config/runtime issue | `rewrite`, `error_page`, FastCGI/script errors                      |
| `502 Bad Gateway`                              |                   Upstream unreachable or invalid response | `proxy_pass`, `upstream`, `proxy_next_upstream`                     |
| `503 Service Unavailable`                      |      Upstream unavailable / request limiting / maintenance | `limit_req`, `limit_conn`, `error_page`                             |
| `504 Gateway Timeout`                          |                                           Backend too slow | `proxy_connect_timeout`, `proxy_read_timeout`, `proxy_send_timeout` |
| `499 Client Closed Request` *(NGINX-specific)* |                      Client disconnected before completion | No direct directive; visible in logs                                |



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
