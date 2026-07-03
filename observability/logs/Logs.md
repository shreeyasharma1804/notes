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
