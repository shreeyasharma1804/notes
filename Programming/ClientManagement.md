### HTTP 1.1 with Connection: close/ keep-alive

- connect() and check for errors
- TLS handhsake
- Write request withing send timeout
- Read response within read timeout
- How to detect that the entire response has been sent
- How to detect that the connection is closed by the server
- What happens if I call send on a socket which is closed by rempte


keep-alive: Again, detecting that the connection is closed and remove the socket from the pool

