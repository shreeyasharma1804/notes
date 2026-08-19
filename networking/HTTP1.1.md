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

What can a get endpoint which stream a file look like ?
