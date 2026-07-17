### General squid proxy config

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
http_access deny CONNECT !SSL_ports        # allow connect method for SSL only
http_access allow localhost manager
http_access deny manager
http_access allow localnet                 # allow above source IPs
http_access allow localhost                # allow localhost 
http_access deny all                       # deny everything else  

# Logging
access_log /var/log/squid/access.log squid 
cache_log /var/log/squid/cache.log
cache_store_log /var/log/squid/store.log

# Hostname
visible_hostname squid-proxy

# Administrative settings
coredump_dir /var/spool/squid
```

### Deployment

- The configmap defines the squid configuration
- Scalable deployment with HPA:

```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: squid-deployment
  namespace: egress
  labels:
    app: squid
spec:
  replicas: 3
  selector:
    matchLabels:
      app: squid
  template:
    metadata:
      labels:
        app: squid
    spec:
      containers:
      - name: squid-container
        image: ubuntu/squid:7.2-26.04_edge
        ports:
        - containerPort: 3128
        volumeMounts:
          - name: config
            mountPath: "/etc/squid"
      volumes:
        - name: config
          configMap:
            name: egress-config
```

- ClusterIP

```yml
apiVersion: v1
kind: Service
metadata:
  name: egress-service
  namespace: egress
spec:
  selector:
    app: squid
  ports:
    - protocol: TCP
      port: 443
      targetPort: 3128
```

- Use PVC for logs and cache storage

- Usage in temporary pod

```bash
kubectl run curl-test \                                                           
  --image=curlimages/curl:latest \
  --restart=Never \
  -it --rm \
  -- sh

$ nslookup egress-service.egress.svc.cluster.local
$ curl -v -x http://egress-service.egress.svc.cluster.local:443 http://httpbin.org/ip
```

- Metrics:
  - Log collection with opentelemetry
  - Metrics collection with prometheus for CPU, RAM and Network I/O

- The egress pods might only be scheduled on nodes which are directly connected to edge routers with NAT enabled so that all egress packets have the same client IP (The routers SNAT address).
