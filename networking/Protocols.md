### Webhooks

Instead of polling the server, we can define a webhook, which sends a POST call based on the event.

Usage in git:

```bash
Configure webhook in git which sends a POST call to a server when a push event occurs -> Server registers the CI job based on the POST call data
```

### Websockets

```python
import asyncio
import websockets

clients = {}

# A host runs the read and send coroutines for all the clients which nonnected to it.
# The read coroutine only consumes cpu when the websocket.recv() buffer is readable.
# The send function subscribes to a resid queue and sends data to the correct websocket(based on cache).

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
