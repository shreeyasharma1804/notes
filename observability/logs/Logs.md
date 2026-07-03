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
