## Application metrics 

```python
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry import metrics

exporter = OTLPMetricExporter(
    endpoint="http://otel-collector:4317",
    insecure=True
)

reader = PeriodicExportingMetricReader(
    exporter,
    export_interval_millis=5000
)

provider = MeterProvider(
    metric_readers=[reader]
)

metrics.set_meter_provider(provider)

from opentelemetry.metrics import get_meter
import time

meter = get_meter("main-service")

total_requests = meter.create_counter("http_requests_total")
latency = meter.create_histogram("http_requests_duration_ms")
errors = meter.create_counter("errors")
active_requests = meter.create_up_down_counter("http_requests_active")
db_latency = meter.create_histogram("db_requests_duration_ms")
# db total requests, errors, latency
# External API latency, errors
cache_hits = meter.create_counter("cache_hits_total")
cache_misses = meter.create_counter("cache_misses_total")
# Queue size, payload size

def get_products():
    total_requests.add(1)
    active_requests.add(1)
    try:
        start = time.perf_counter()
        # Business logic start
        time.sleep(2)
        # Cache fetch start
        if cache_found():
            cache_hits.add(1)
        else:
            cache_misses.add(1)
        # Cahe fetch end
        # db query start
        db_start = time.perf_counter()
        time.sleep(5)
        db_latency.record((time.perf_counter()-db_start)*1000)
        # db query end
        # Business logic ends
        latency.record((time.perf_counter()-start)*1000)
    except:
        errors.add(1)
    finally:
        active_requests.add(-1)


while(True):
    get_products()
    time.sleep(5)
```


```bash
Application -> sends metrics to otel collector -> otel collector exposes the metrics on one port -> prometheus scrapes the port and stores the data in a TSDB

prometheus also scrapes /metrics/cadvisor on every kubelet for container resource usage metrics

Overall node statistics require daemonset of node exporter
```

```yml
# otel-configmap

apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-config
  namespace: metric

data:
  otel-config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

    exporters:
      prometheus:
        endpoint: "0.0.0.0:9464"

      debug:
        verbosity: detailed

    service:
      telemetry:
        logs:
          level: debug

      pipelines:
        metrics:
          receivers: [otlp]
          exporters: [debug, prometheus]

# prometheus configmap
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: metric

data:
  prometheus.yml: |
    global:
      scrape_interval: 5s

    scrape_configs:

    - job_name: otel

      static_configs:
      - targets:
        - otel-collector:9464

    - job_name: kubelet

      scheme: https

      kubernetes_sd_configs:
      - role: node

      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

      tls_config:
        insecure_skip_verify: true

      relabel_configs:

      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

      - target_label: __address__
        replacement: kubernetes.default.svc:443

      - source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
        replacement: /api/v1/nodes/$1/proxy/metrics/cadvisor
```

## K8S metrics (Advisor and cAdvisor)

### Setup

#### Prerequisites

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/proxy
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
```

#### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:

      # Kubelet metrics
      - job_name: kubernetes-kubelet
        scheme: https

        # metrics_path not defined here because the default is /metrics

        kubernetes_sd_configs:       # Service Discovery config (equivalent to describing all the nodes in the cluster)
          - role: node

        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token   # Bearer token for connecting to API server

        tls_config:
          insecure_skip_verify: true

        relabel_configs:
          - source_labels: [__address__]          # Relabel the __address__ field of all discovered nodes from ip:<port> to ip:<10250> which is the kubelet server port
            regex: '(.*):.*'
            target_label: __address__
            replacement: '${1}:10250'

          - source_labels: [__meta_kubernetes_node_name]      # Rename the label __meta_kubernetes_node_name to node
            target_label: node


      # Kubelet cAdvisor metrics
      - job_name: kubernetes-cadvisor
        scheme: https

        metrics_path: /metrics/cadvisor

        kubernetes_sd_configs:
          - role: node

        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token

        tls_config:
          insecure_skip_verify: true

        relabel_configs:
          - source_labels: [__address__]
            regex: '(.*):.*'
            target_label: __address__
            replacement: '${1}:10250'

          - source_labels: [__meta_kubernetes_node_name]
            target_label: node
```

#### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus

  template:
    metadata:
      labels:
        app: prometheus

    spec:
      serviceAccountName: prometheus

      containers:
        - name: prometheus
          image: prom/prometheus:v3.5.0

          args:
            - --config.file=/etc/prometheus/prometheus.yml
            - --storage.tsdb.path=/prometheus
            - --web.enable-lifecycle

          ports:
            - name: http
              containerPort: 9090

          volumeMounts:
            - name: config
              mountPath: /etc/prometheus

            - name: data
              mountPath: /prometheus

      volumes:
        - name: config
          configMap:
            name: prometheus-config

        - name: data
          emptyDir: {}
```

Note:
- Default TSDB retention time: 15 days
- PVC is required for the tsdb storage

#### Service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
spec:
  type: ClusterIP
  selector:
    app: prometheus
  ports:
    - name: http
      protocol: TCP
      port: 9090
      targetPort: 9090
```

### Important metrics exposed at /metrics:

- kubelet_active_pods: Total number of pods currently running
- kubelet_desired_pods: Total number of pods that should be running

### Important metrics exposed at /metrics/cAdvisor

- For control-plane metrics, use: `node_role_kubernetes_io_control_plane="true"`
- For CoreDNS, use: `rate(container_network_transmit_bytes_total{pod=~"coredns.*"}[5m])`

#### CPU (Counter)

- Top 10 CPU consuming containers:

```bash
topk(10, rate(container_cpu_usage_seconds_total[5m]))
```

- CPU usage of a container

```bash
rate(container_cpu_usage_seconds_total{container="hi-bye-app"}[5m])
```

- CPU usage of a namespace:

```bash
sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m]))
```

- CPU usage of the entire namespace

```bash
sum by (namespace)((rate(container_cpu_usage_seconds_total[5m])))
```

- CPU Usage of all pods:

```bash
sum by (pod, namespace)((rate(container_cpu_usage_seconds_total[5m])))
```

#### Memory (guage)

container_memory_working_set_bytes = total_usage - file cache

container_memory_working_set_bytes provides the actual pod RAM Usage. In case if a pod is about to be OOM killed, the kernel first releases the file cache. OOM killing depends on the actual pod memory usage then

```bash
sudo sysctl -w vm.drop_cache=3
```


- Memory usage of pods

```bash
sum by (pod, namespace) (container_memory_working_set_bytes)
```

- Total memory usage:

```
sum (sum by (pod, namespace) (container_memory_working_set_bytes))
```


- Top 10 CPU Usage per pod and per cluster

```
topk(
  10,
  sum by (cluster, pod) (
    rate(container_cpu_usage_seconds_total{image!=""}[5m])
  )
)
```

- Top 10 memory usage per pod and per cluster

```
topk(
  10,
  sum by (cluster, pod) (
    rate(container_memory_working_set_bytes{image!=""}[5m])
  )
)
```

#### File system usage (Guage)

- `container_fs_usage_bytes`: Total writable layer size, it does not include any directory mounted by a PVC
- `container_fs_reads_total`: Total number of reads performed by the container, also includes reads in the PVC
- `container_fs_reads_bytes_total`: Total number of bytes reads by the container, also includes bytes read from the PVC

- Per container

```bash
container_fs_usage_bytes
```

- Per pod

```bash
sum by (pod) (container_fs_usage_bytes)
```

- Top 10 containers

```bash
topk(10,(container_fs_usage_bytes))
```

- Inode usage (To monitor inode exhaution, which prevents creation of new files even if disk space is available)

```bash
((container_fs_inodes_total-container_fs_inodes_free)/container_fs_inodes_total)*100
```

- Number of file system reads per second

```bash
rate(container_fs_reads_total[5m])
```

- Number of file system writes per second

```bash
rate(container_fs_writes_total[5m])
```

- Pod with highest numner of write rate

```bash
topk(10,(sum by (pod) (rate(container_fs_writes_total[5m]))))
```

- Disk growth trend (use deriv with guages)

```
deriv(container_fs_usage_bytes[1h])
```

- Check how much usage increased in the last 1 hour

```
delta(container_fs_usage_bytes{container!=""}[1h])
```

- Predict future disk usage

```
predict_linear(container_fs_usage_bytes[6h], 24 * 3600)
```

#### Networks (counters)

- Total bytes recieved in a container

```bash
rate(container_network_receive_bytes_total[5m])
```

- Total number of bytes sent by the container

```bash
rate(container_network_transmit_bytes_total[5m])
```

#### PVC Monitring

```bash
└❯ cd ~ && curl -k --cert admin.crt --key admin.key https://192.168.1.9:10250/metrics > metrics.txt
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 6903k    0 6903k    0     0  52.4M      0 --:--:-- --:--:-- --:--:-- 52.6M

┌💁  shreeya @ 💻  pop-os in 📁  ~
└❯ cat metrics.txt | grep kubelet_volume_stats_used_bytes
# HELP kubelet_volume_stats_used_bytes [ALPHA] Number of used bytes in the volume
# TYPE kubelet_volume_stats_used_bytes gauge
kubelet_volume_stats_used_bytes{namespace="kubevious",persistentvolumeclaim="data-kubevious-mysql-0"} 2.83065274368e+11
kubelet_volume_stats_used_bytes{namespace="openebs",persistentvolumeclaim="export-openebs-minio-0"} 2.83063701504e+11
kubelet_volume_stats_used_bytes{namespace="openebs",persistentvolumeclaim="export-openebs-minio-1"} 2.830646272e+11
kubelet_volume_stats_used_bytes{namespace="openebs",persistentvolumeclaim="export-openebs-minio-2"} 2.83061936128e+11
kubelet_volume_stats_used_bytes{namespace="openebs",persistentvolumeclaim="storage-openebs-loki-0"} 2.83034345472e+11
```

- ETCD Dashboard
