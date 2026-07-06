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
