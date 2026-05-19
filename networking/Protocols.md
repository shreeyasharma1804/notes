### Webhooks

Instead of polling the server, we can define a webhook, which sends a POST call based on the event.

Usage in git:

```bash
Configure webhook in git which sends a POST call to a server when a push event occurs -> Server registers the CI job based on the POST call data
```

### Simple REST

```python
@get
def serve_get_request():
    # Process
    # return
```

Is basically:

```python
def get(connection_object, server_get_request):

    async for message in connection_object:
        # await Read utnil HTTP request is complete or connection_object.recv()

    return_obj = server_get_request()

    await connection_object.send(return_obj)

```

### Websockets

- Websockets require additional headers in nginx like 101 Upgrade connection.
- Every time a new connection comes, the websockets server calls handle_connection with the connection object (Similar to accept returing the connection fd).
- Since websocket objects are local to a host, they are stored in a local cache with the mapping <client-identifier> -> websocket object
- The read and write coroutine runs for every client connected to the host
- The handle_connection function is responsible for adding the websocket to the cache and scheduling the read and write coroutines
- The read coroutine runs connection_fd.recv() which returns EAGAIN if the socket is not readable. The connection_fd is added to the websocket queue when the socket is readabale. This allows the server to read the socket asyncronously.
- In case if I can add a return statement based on some logic, the read coroutine exits and the server behaves similar to SSE
- The write corotuine is also asynchronous, it can waiton something like asyncio.queue and trigger if any data is available.
- The redis library has support for async pub-sub functions

Initial headers:

Request:
```http
GET /chat HTTP/1.1
Host: localhost:8000
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==
Sec-WebSocket-Version: 13
```

Response:
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=
```

```python
import asyncio
import websockets

clients = {}

# A host runs the read and send coroutines for all the clients which connected to it.
# The read coroutine only consumes cpu when the websocket.recv() buffer is readable.
# The send function subscribes to a redis queue and sends data to the correct websocket(based on cache).
# Redis only holds client: host mapping. websocket objects are not cached and are local to the host which created it
async def send_to_client(client_id):

    # Await on something like a redis queue, if data found, send to the client

    websocket = clients.get(client_id)

    if websocket:
        await websocket.send("Hello from server")
    else:
        print("Client not found")


async def read_from_client(client_id):

    websocket = clients.get(client_id)

    async for message in websocket:
        print(f"{client_id}: {message}")


async def handle_connection(websocket):

    client_id = websocket.request.headers.get("user")

    clients[client_id] = websocket

    read_data = asyncio.create_task(read_from_client(client_id))
    send_data = asyncio.create_task(send_to_client(client_id))

    await read_data
    await send_data


async def main():
    server = await websockets.serve(handle_connection, "localhost", 8765)
    await server.wait_closed()

asyncio.run(main())
```

### SSE

Generic HTTP streaming:

```http
GET /stream HTTP/1.1
Host: localhost

HTTP/1.1 200 OK
Content-Type: text/plain
Transfer-Encoding: chunked
```

The data is sent in the response body and needs to be handled at the client specifically

SSE is a subset of HTTP streaming with browser support

```http
GET /events HTTP/1.1
Host: localhost
Accept: text/event-stream

HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```
