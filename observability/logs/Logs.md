### python logger

- Call the logger in each module (useful in exporting the logs)

```python
import logging

logger = logging.getLogger(__name__)
```

- logger support log levels
- basicConfig:

```
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

### Opentelemtry Collector

Colector collects logs from the application and processes them before exporting to a ingestion service like splunk. (Similar to splunk daemon for log collection)

```bash
docker run --rm \
  --name otel-collector \
  -p 4317:4317 \
  -p 4318:4318 \
  -v $(pwd)/otel-collector.yaml:/etc/otelcol-contrib/config.yaml \
  otel/opentelemetry-collector-contrib:latest
```

Config file:

```yml
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:

exporters:
  debug:

service:
  pipelines:
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
```

- receivers: Enable recieving logs in collector on otlp protocol with grpc and http protocols
- batch processor: Enable batching before exporting logs
- exporters: Define the exporter, elasticseaerch etc. debug means stdout
