###  Tracing

- Use along with Nginx request-id to fully trace a request.

### Python App with tracing

```python
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def setup_telemetry(service_name: str):
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
            }
        )
    )

    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="localhost:4317",
                insecure=True,
            )
        )
    )

    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)
```

```python
from fastapi import FastAPI
import requests
import time

from common.telemetry import setup_telemetry

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

tracer = setup_telemetry("order-service")

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)
RequestsInstrumentor().instrument()


@app.get("/order")
def order():
    with tracer.start_as_current_span("Validate User"):
        time.sleep(0.5)

    with tracer.start_as_current_span("Call Inventory"):
        r = requests.get("http://localhost:8001/inventory")

    return r.json()
```

```python
from fastapi import FastAPI
import time

from common.telemetry import setup_telemetry

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = setup_telemetry("inventory-service")

app = FastAPI()

FastAPIInstrumentor.instrument_app(app)


@app.get("/inventory")
def inventory():
    with tracer.start_as_current_span("Check Database"):
        time.sleep(1)

    return {"stock": 25}
```

### Data flow

```
+-------------------+
| Order Service     |
| OTLP Exporter     |
+-------------------+
          |
          | Export to OTLP (4317)
          |
+-----------------------+
| OpenTelemetry Collector|
+-----------------------+
          ^
          |
          | Jaeger reads data from configured collector port and displays in UI
          |
+----------------+
| Jaeger         |
+----------------+
          |
          v
     Jaeger UI
```

OTEL Pipeline:

- Application sends data to a collector port, might be a specific REST endpoint which is configured in the receivers section
- Application scrapes data from a collector port, might be a diffferent specific REST endpoint which is configured in the exporters section

```yml
receivers:
  otlp:
    protocols:
      grpc:
      http:

exporters:
  otlp:
    endpoint: jaeger:4317
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlp]
```
