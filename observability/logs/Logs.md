### Overview

- When the handler is configured to send logs to the otel collector,  each logger.<>("message") is treated as a seperate event. No multiline parses are required.
- When the handler is configured to send logs to a file, which the otel collector later scrapes, multi line parses are required. In production, the logs should be formated such that the multi-line parser regular  expression knows when a new event starts

```
Recommended format: 2026-07-10T12:30:16.456Z ERROR order-service requestId=abc123 traceId=5b8aa... Failed to process order
Regex: ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d+Z\s+(ERROR|INFO)\s\S+\s(requestId=)\S+\s\S+
```

- otel sends the log with other data visible with the verbose option.

### python logger

- Call the logger in each module (useful in exporting the logs)

```python
import logging

logger = logging.getLogger(__name__)
```

- logger support log levels
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

- Production log format: `2026-07-10T12:30:16.456Z ERROR order-service requestId=abc123 traceId=5b8aa... Failed to process order`

### Opentelemetry exporter in python

```python
import logging

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter


def configure_logging():

    # Exporter location
    exporter = OTLPLogExporter(
        endpoint="http://localhost:4317",
        insecure=True,
    )

    # Resource broadly defines the service which is appended to all the logs emitted by the exporter
    resource = Resource.create({
        "service.name": "order-service",
        "service.version": "1.0"
    })

    # Define log processor
    processor = BatchLogRecordProcessor(exporter)

    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(processor)

    handler = LoggingHandler(
        logger_provider=provider
    )

    # Configure the global logger using basicConfig and define the handler as the  otel provider
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )
```

- Usage

```python
configure_logging()
logger = logging.getLogger(__name__)
```

### Opentelemtry Collector

- Colector collects logs from the application and processes them before exporting to a ingestion service like splunk. (Similar to splunk daemon for log collection)

- Config file:

```yml
# Define the endpoint the collector is running on and the protocols it supports
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

# Define the processing to be performed on the logs before exporting to external service
processors:
  batch:

# Define the external service, debug means stdout
exporters:
  debug:
    verbosity: detailed

# Define the entire pipeline
service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
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
