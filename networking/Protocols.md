### Webhooks

Instead of polling the server, we can define a webhook, which sends a POST call based on the event.

Usage in git:

```bash
Configure webhook in git which sends a POST call to a server when a push event occurs -> Server registers the CI job based on the POST call data
```

### Websockets

```
# server.py
import asyncio
import websockets
from datetime import datetime


async def receive_messages(websocket):
    try:
        async for message in websocket:
            print("Client:", message)

    except websockets.ConnectionClosed:
        print("Receive loop ended")


async def send_messages(websocket):
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")

            await websocket.send(
                f"Server time: {current_time}"
            )

            await asyncio.sleep(3)

    except websockets.ConnectionClosed:
        print("Send loop ended")


async def handle_connection(websocket):
    print("Client connected")

    await asyncio.gather(
        receive_messages(websocket),
        send_messages(websocket)
    )


async def main():
    server = await websockets.serve(
        handle_connection,
        "localhost",
        8765
    )

    print("Running on ws://localhost:8765")

    await server.wait_closed()


asyncio.run(main())
```
