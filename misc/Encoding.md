### UTF-8

- Variable length encoding scheme (1-4 bytes)
- ASCII compatible characters are stored in 1 byte, backward compatibility

### Message pack

Efficient storage of json data

```
convert python object to msgpack object -> store in redis/memcached -> retrive -> convert to python object -> read data
```

This pipeline is faster in msgpack compared to json
