```squid

# The port squid listens on
http_port 3128

# Cache direcotry with unix file system at /var/spool/squid of maximum 10GB size (cache is evicted if this number is reached), 16 first level directories and 256 second level directories
cache_dir ufs /var/spool/squid 10000 16 256

# maximum in memory cache
cache_mem 256 MB

maximum_object_size 100 MB
minimum_object_size 0 KB

# Maximum size of one object that can be cached in memory
maximum_object_size_in_memory 512 KB

# Disk cache is evicted based on Least frequently used cache with dynamic aging
cache_replacement_policy heap LFUDA

# Greedy dual size frequnecy, i.e, small latest cached items will be given priority in retention
memory_replacement_policy heap GDSF

# Declare source IPs
acl localnet src 10.0.0.0/8   
acl localnet src 172.16.0.0/12
acl localnet src 192.168.0.0/16
acl localnet src fc00::/7
acl localnet src fe80::/10

acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 21          # ftp
acl Safe_ports port 443         # https
acl Safe_ports port 70          # gopher
acl Safe_ports port 210         # wais
acl Safe_ports port 1025-65535  # unregistered ports
acl Safe_ports port 280         # http-mgmt
acl Safe_ports port 488         # gss-http
acl Safe_ports port 591         # filemaker
acl Safe_ports port 777         # multiling http
acl CONNECT method CONNECT

http_access deny !Safe_ports               # allow connections to only safe ports
http_access deny CONNECT !SSL_ports        # CONNECT is used in 
http_access allow localhost manager
http_access deny manager
http_access allow localnet
http_access allow localhost
http_access deny all

# Logging
access_log /var/log/squid/access.log squid
cache_log /var/log/squid/cache.log
cache_store_log /var/log/squid/store.log

# Hostname
visible_hostname squid-proxy

# Administrative settings
coredump_dir /var/spool/squid

# Refresh patterns for caching
refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320
```
