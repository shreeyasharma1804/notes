What should be logged in k8s ?

- /var/log/pods
- journald logs for containerd and kubectl

How to read the files (receivers: file log)
- encoding
- regex location (both include and exclude)


What should an exporter support?
- The endpoint
- compression
- max idle connections
- idle timeouts
- number of retries, intervals between them
- queue (this data structure supports retries) with number of consumers and max size
- timeout


Required extensions:

- file_storage: Provides a location for otel to store the offsets of the various fds it is reading
- health_check: Provides an HTTP endpoint for otel healthchecks (Just checks if the otel process is up)
- k8s_observer: Log enrichment


Processors: Log processing
- batching
- enriching
