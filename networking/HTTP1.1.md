### Client

- connect()
- Non Blocking TLS handshake
- Send request within send timeout
- Read response within read timeout
- The response headers are complete after \r\n\r\n
- With Connection: Close, the remote server sends FIN. This makes the socket readable but with no data. Thus, Content-Length header need not be parsed to read x number of bytes, as soon as the response is complete, the server will close the connection, which triggers EPOLLIN
- EPOLLIN keeps triggering because the socket is readable, thus, EPOLLIN with empty data should be used to close the socket
- For Connection: keepalive, the remote server keeps the connection open. Content-Length needs to be parsed to get the complete response
- When a server closes a connection, it sends FIN and the client sends ACK as soon as the FIN reaches it.
- Calling socket.close() sends FIN from the client, which the server acknowledges. This completes the 4-way connection closing handshake.
- A client can call send() after a connection has been closed by remote, because, because TCP is duplex, reads and writes are simultaneous. The server will respond with a RST because application has called close() on that socket.
- Requests to a closed TCP connection fail silently if RST is not used by remote server

```python
import socket
import ssl
import select

host = "httpbin.org"

epoll = select.epoll()

# Create TCP connection
sock = socket.create_connection((host, 443))

# Wrap it in TLS
context = ssl.create_default_context()
tls_sock = context.wrap_socket(sock, server_hostname=host)

request = (
    "GET /get HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    "\r\n"
).encode("ascii")

tls_sock.sendall(request)

epoll.register(tls_sock.fileno(), select.EPOLLIN)

while 1:
    events = epoll.poll()
    for fd, event in events:
        data = tls_sock.recv(64)
        if data == b'':
            print("Response complete")
        data = data.decode("utf-8")
        if(data[-4:-1] == "\r\n\r\r\n"):
            print("Response header complete")
        print(data)
        print("--------------------------")


tls_sock.close()
```

### Server

```python
import socket
import select

epoll = select.epoll()

server = socket.socket()

server.bind(("0.0.0.0", 9999))
server.listen(50)

server.setblocking(False)

epoll.register(server.fileno(), select.EPOLLIN)

client_fd_mapping = {}

request_buffers = {}

def get(request):
    # Parse headers from the request
    # Create a future which holds the response
    # yeild wherever required
    # Complete the future
    # Add the response to the response buffer
    # modify the connection_socket to trigger on EPOLLOUT
    # Write data to the socket buffer
    # If Connection: close, close the connection_socket()
    # If Connection: keep-alive, start a timer, and if the timer expires, close the connection_socket()
    pass

while True:
    events = epoll.poll()

    for fd, event in events:
        if(fd == server.fileno()):
            connection_socket, _ = server.accept()
            connection_socket.setblocking(False)
            epoll.register(connection_socket.fileno(), select.EPOLLIN)
            request_buffers[connection_socket.fileno()] = ""
            client_fd_mapping[connection_socket.fileno()] = connection_socket
        else:
            connection_socket = client_fd_mapping[fd]
            request_data = connection_socket.recv(64)
            print(request_data)
            request_buffers[connection_socket.fileno()] = request_buffers[connection_socket.fileno()] + request_data.decode("utf-8")

            if(b"\r\n\r\n" in request_data):
                print("Request recieved")

                # get is a coroutine which has to be added to the event loop
                get(request_buffers[connection_socket.fileno()])

            # If the client closes the connection while sending the request
            if(request_data == b""):
                print("Connection closed")
                epoll.unregister(connection_socket.fileno())
                connection_socket.close()

```

### Streaming

What can a get endpoint which streams a file look like ?


```python
import time
'''
    Practical scenario:
    while True:
        data = os.read(fd, 64 * 1024)  # Read only 64 KB at a time

        if data == b"":
            break  # EOF

    The kernel creates a new file descriptor for every process which may be opening the same file
    It tracks the offset till which the file has been read
    When multiple read calls are issued, the starting offset is maintained by the kernel and advanced accordingly
'''


file_data = "This is a very huge file which needs to be streamed rather than letting the os fully read it before "

def stream_data_endpoint():
    # In response headers, set Transfer-Encoding: chunked
    # Return 2 letters per chunk
    for i in range(0, len(file_data), 2):
        lines = [file_data[i], file_data[i+1]]
        yield lines

coroutine = stream_data_endpoint()


# The event loop calls next on the function
try:
    data = next(coroutine)
    # Add to response buffer
    time.sleep(1)
except StopIteration:
    print("Request complete")
    # Send socket.send(b"0\r\n\r\n") to indicate that the stream is complete

# When EPOLLOUT triggers on the socket file descriptor, write to the socket fd
# sent = socket.send(response_buffer).
# Remove send number of bytes from the buffer to indicate that the data has been sent
```

### SSE

General consideration: At the server end, how to reduce EPOLLOUT triggers when there is no data in the response buffer. Add data to the buffer and then modify for the trigger ?

- Unlike streaming, where the server sends chunks of data because the processing is not complete, also, maybe because the response size is larger than the socket write buffer size, SSEs send event data, where every chunk is a separate event (not a chunk, a complete set of data for one event).
- The separator between 2 events is \n\n

Server:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()


async def event_generator():
    counter = 0

    while True:
        # Add some useful processing here
        counter += 1

        yield f"data: Message {counter}\n\n"

        await asyncio.sleep(1)


@app.get("/events")
async def events():
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

Client: Upon receiver data, call a callback function ?

### WebSockets
