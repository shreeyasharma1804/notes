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
	ssl_prefer_server_ciphers on;

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
	include /etc/nginx/sites-enabled/*;
}
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
