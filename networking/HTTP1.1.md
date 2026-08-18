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
- If the client sends data after the server has sent FIN, the server sends RST which is visible as ConnectionResetError in Python

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
