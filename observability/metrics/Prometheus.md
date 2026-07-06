### Data types

- Scalar: Integer
- Instant vector: One single vector returned from a query response
```
node_cpu_seconds_total
```
- Range vector: Array of instant vectors retirned from a query response over a time range
```
node_cpu_seconds_total[5m]
```
- Counters: Monotonically increasing values
- Guages: Values range between [a,b]

### Functions for counters and gauges

- If a function does not handle reset, it treats it like any other value
- If a function handles a reset, it skips the values where a reset might have occured, example, future value is less in a counter

1. delta(v[5m]) – Returns the difference between the last and first sample in the range vector. Intended for gauges; does not handle counter resets.
2. idelta(v[5m]) – Returns the difference between the last two samples in the range vector. Intended for gauges; does not handle counter resets.
3. increase(v[5m]) – Returns the total increase of a counter over the range, handling counter resets, increase: sum(v(i+1) -v(i)) over the range vector (Handles resets)
4. deriv(v[5m]): Calculates the liner regression slope of the range vector, does not handle resets
5. rate(v[5m]): increase function output​/elapsed time, handles resets
6. irate(v[5m]): idelta output/ sampling time, handles resets
7. predict_linear(v[5m], t): Returns the linear regression prediction of the range vector after t time
8. resets(v[5m]): Total resets in the range vector

### Other functions

1. absent: Return 1 if instant vector is empty
2. absent_over_time: Return 1 if range vector is empty
3. clamp: Clamp all instant vector between a min and max value
4. sort: Sort the index vector returned by multiple series, used to organize data for tasks like finding the container with highest CPU usage
5. abs
6. ceil
7. floor
8. exp
9. ln
10. log2
11. log10

### Histograms

- Values are sampled in buckets, each bucket is a seperate time series
- The sampling rate of a bucket is fixed
- For every histogram, prometheus stores:

For example, for the latency values:

```
12
35
80
20
40
```

1. Bucket counts: (These counts are cumulative)

```
http_request_duration_bucket{le="10"}    0
http_request_duration_bucket{le="25"}    2
http_request_duration_bucket{le="50"}    4
http_request_duration_bucket{le="100"}   5
http_request_duration_bucket{le="+Inf"}  5
```

2. http_request_duration_sum: The sum of all input data, here 187
3. http_request_duration_count: Total number of values added to the histogram, here, 5



