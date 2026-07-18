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
# Define the file the collector reads
receivers:
  filelog/squid:
    include:
        - /var/log/pods/egress_squid_deployment*/squid-container/*.log
    start_at: beginning
    multiline:
        line_start_pattern: 


# Define the processing to be performed on the logs before exporting to external service
processors:
  batch:

# Define the external service to which otel exports the logs for persistant storage, like elasticsearch, also, debug means stdout
exporters:
  debug:
    verbosity: detailed

# Define the entire pipeline
service:
  pipelines:
    logs:
      receivers:
      - filelog/squid
      processors:
       - batch
      exporters:
       - debug
```

- Run as a docker image

```bash
docker run --rm \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  -v $(pwd)/otel-collector.yaml:/etc/otelcol-contrib/config.yaml \
  otel/opentelemetry-collector-contrib:latest
```

- Log output:

```bash
Timestamp: 2026-07-03 11:12:01.76553728 +0000 UTC
SeverityText: INFO
SeverityNumber: Info(9)
Body: Str(INFO:__main__:Processing order 15)
Attributes:
     -> code.file.path: Str(/home/shreeya/Downloads/opentelemetry/logs/main.py)
     -> code.function.name: Str(process_order)
     -> code.line.number: Int(8)
Trace ID:
Span ID:
Flags: 0
LogRecord #1
ObservedTimestamp: 2026-07-03 11:12:01.765765864 +0000 UTC
Timestamp: 2026-07-03 11:12:01.765736192 +0000 UTC
SeverityText: INFO
SeverityNumber: Info(9)
Body: Str(INFO:__main__:Order processed successfully)
Attributes:
     -> code.file.path: Str(/home/shreeya/Downloads/opentelemetry/logs/main.py)
     -> code.function.name: Str(process_order)
     -> code.line.number: Int(14)
```

### ElasticSearch and Kibana

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
