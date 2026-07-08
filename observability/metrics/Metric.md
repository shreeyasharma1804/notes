### Metrics emitted by application using opentelemetry

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

### K8S setup

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

### K8S Metrics

#### CPU (Counter)

- Top 10 CPU consuming containers:

```bash
topk(10, rate(container_cpu_usage_seconds_total[5m]))
```

- CPU usage of a container

```bash
rate(container_cpu_usage_seconds_total{container="hi-bye-app"}[5m])
```

- CPU usage of a namepsace:

```bash
sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m]))
```

- CPU usage of the entire namespace

```bash
sum by (namespace)((rate(container_cpu_usage_seconds_total[5m])))
```

- CPU Usage of all pods:

```bash
sum by (pod)((rate(container_cpu_usage_seconds_total[5m])))
```

#### Memory (guage)

container_memory_working_set_bytes = total_usage - file cache

container_memory_working_set_bytes provides the actual pod RAM Usage. In case if a pod is about to be OOM killed, the kernel first releases the file cache. OOM killing depends on the actual pod memory usage then

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

- Network I/O

- PVC Monitroing ?
- CoreDNS
- ETCD Dashboard
- Control Plane monitoring
