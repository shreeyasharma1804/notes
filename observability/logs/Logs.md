### Overview

- When the handler is configured to send logs to the otel collector,  each logger.<>("message") is treated as a seperate event. No multiline parses are required.
- When the handler is configured to send logs to a file, which the otel collector later scrapes, multi line parses are required. In production, the logs should be formated such that the multi-line parser regular  expression knows when a new event starts

```
Recommended format: 2026-07-10T12:30:16.456Z ERROR order-service requestId=abc123 traceId=5b8aa... Failed to process order
Regex: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z\s+(ERROR|INFO)\s\S+\s(requestId=)\S+\s\S+
```

- otel sends the log with other data visible with the verbose option.

### python logger

- basicConfig:

```python
import logging

# Define the lowest log levels that can be used, enfore formatting
# handlers define where to flush the logs, stdout, a file or otel
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),   # Logs to stdout
        logging.FileHandler("app.log"),      # Logs to app.log
    ],
)
```

- the basicConfig is declared once per project and applies to all the loggers returned by getLogger()

### Log Management

- stdout logs of a pod are stored at: `/var/log/pods/<pod-name>/<container-name>/*.log`
- The log rotation policy is defined in the kubelet config:

```bash
containerLogMaxSize: 10Mi
containerLogMaxFiles: 5
```
- If an application writes to a file, a default hostPath can be used to write all the logs to a particular location from where the collector can read

### Opentelemtry Collector

- The files from which the logs are collected and the regex for multi line parsing is defined in the collector config.
- The collector runs as a daemonset on all the nodes
- All the daemonsets can refer to the same configmap, since the collector does not fail if a filelog regex is not found
- By default, the offset which the collector has read is stored in-memory. If the collector restarts, these offsets might be lost, to avoid this, the file_storage extension is used, which tracks this offset in a file

- Config file:

```yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-config
  namespace: metrics
data:
  config.yaml: |
    extensions:
      file_storage:
        directory: /tmp/otelcol/file_storage
        create_directory: true

    receivers:
      filelog/squid:
        include:
          - /var/log/pods/egress_squid-deployment*/squid-container/*.log

        start_at: beginning

        storage: file_storage

        multiline:
          line_start_pattern: '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+(?:Z|[+-]\d{2}:\d{2})'


    processors:
      batch:

    exporters:
      debug:
        verbosity: detailed

    service:
      extensions:
        - file_storage
      telemetry:
        logs:
          level: debug

      pipelines:
        logs:
          receivers:
            - filelog/squid
          processors:
            - batch
          exporters:
            - debug
```

- Pod

```yml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: otel-daemonset
  namespace: metrics
  labels:
    app: otel-collector
spec:
  selector:
    matchLabels:
      app: otel-collector

  template:
    metadata:
      labels:
        app: otel-collector

    spec:
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector-contrib:0.130.0

          args:
            - --config=/etc/otelcol-contrib/config.yaml

          volumeMounts:
            - name: config
              mountPath: /etc/otelcol-contrib
              readOnly: true

            - name: storage
              mountPath: /tmp/otelcol/file_storage

            - name: podlogs
              mountPath: /var/log/pods
              readOnly: true

      volumes:
        - name: config
          configMap:
            name: otel-config

        - name: storage
          hostPath:
            path: /tmp/otelcol/file_storage
            type: DirectoryOrCreate

        - name: podlogs
          hostPath:
            path: /var/log/pods
            type: Directory
```

- send_queues and rewrites

### ElasticSearch

- Indexes are mandatory when sending data to elasticsearch using the POST request. Define the index in the collector for every file:

```yaml
exporters:
  elasticsearch/pebble:
    endpoints: ["http://elasticsearch:9200"]
    logs_index: pebble-logs

  elasticsearch/nginx:
    endpoints: ["http://elasticsearch:9200"]
    logs_index: nginx-logs
```

- If the index does not exist already, and auto indexing is enabled, the cluster creates the index automatically

```yml
action.auto_create_index: true
```

- The elastic search nodes form a cluster and every node acts as a coordinator to send the write request to the correct shard. The correct shard is chosen based on hash(event)%(number of shards)
- The default number of shards and replicas for a single and multi node cluster is 1. Create an index with the correct number of shards and replicas:

```bash
PUT /logs
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 2
  }
}
```

- By default, elasticsearch sends a success resposne for an ingestion query if the data is successfully written to the write-ahead log and the primary shard DB. Replication happens asynchronously.

- ILM, refresh_rate, what does the leader do, wait_for_active_shards
- Requires leader election for cluster management, raft ?

### Kibana

```bash
podman network create elastic-net

podman run -d \
  --name elasticsearch \
  --network elastic-net \
  -p 9200:9200 \
  -p 9300:9300 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e ES_JAVA_OPTS="-Xms1g -Xmx1g" \
  docker.io/elasticsearch:9.1.0

 podman run -d \
  --name kibana \
  --network elastic-net \
  -p 5601:5601 \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  docker.io/kibana:9.1.0
```
