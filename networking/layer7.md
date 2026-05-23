### HTTP

#### HTTP 1

- HTTP/1.0 default behavior  is one request per TCP connection.
-  Connection is closed after the response.

#### HTTP 1.1

- Persistent connection, `Connection: keep-alive` was default and the connection would close only after `Connection: close`.
- One one request at a time per connection.
- Only one request is served at a time (Req1 -> Res1 -> Req2 -> Res2). If Res1 is slow, Res2 is also blocked. Basically, responses cannot be interleaved.
- This is a text based protocol

```
GET /index.html HTTP/1.1
Host: example.com

The server must:
- scan for spaces
- scan for `\r\n`
- parse strings
- split headers
- interpret textual boundaries
```


#### HTTP 2

- The socket is not locked on per request basis.
- Request-Response pairs are multiplexed.
- Each request-response pair is identified through a unique `streamid`
- Binary framing is used

```
[length][type][flags][stream_id][payload]

The parser knows exactly:

-  byte 1-3 = frame length
-  byte 4 = frame type
-  byte 5 = flags
-  byte 6-9 = stream ID

No text scanning needed.
```

### Client connection timeout

HTTP connection timeouts are defined when calling the url, example `fetch`, `timeout`in Ansible etc

### Streaming

```http
# instead of
Content-Length: <length>

# Use
Transfer-Encoding: chunked
```

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json

class  StreamingHandler(BaseHTTPRequestHandler):

	protocol_version =  "HTTP/1.1"
	
	def do_GET(self):
		if  self.path !=  "/stream":
			self.send_response(404)
			self.end_headers()
			return

		self.send_response(200)
		self.send_header("Content-Type",  "text/plain")
		self.send_header("Transfer-Encoding",  "chunked")
		self.send_header("Connection",  "keep-alive")
		self.end_headers()

		with  open("text.txt",  "r")  as f:
			for line in f.readlines():
				time.sleep(1)
				payload = line.encode()
				chunk =  (
								hex(len(payload))[2:].encode()
								+  b"\r\n"
								+ payload
								+  b"\r\n"
								)
				self.wfile.write(chunk)
				self.wfile.flush()

			# End chunked stream
			self.wfile.write(b"0\r\n\r\n")
			self.wfile.flush()

  

	def run():
		server =  HTTPServer(("0.0.0.0",  8080), StreamingHandler)
		print("Streaming server running on http://localhost:8080/stream")
		server.serve_forever()

if  __name__  ==  "__main__":
	run()
```


### Headers

Inspect headers using

```bash
curl -I <>
```

#### CORS

```
Frontend JS
    ↓
Browser sees cross-origin request
    ↓
Browser sends OPTIONS preflight
    ↓
Server replies with allowed origins/methods/headers
    ↓
Browser validates response
    ↓
Browser sends actual request
    ↓
Browser exposes response to JS
```

Request:

```js
fetch("https://api.com/users", {
    method: "PUT",
    headers: {
        "Authorization": "Bearer abc",
        "X-Custom": "hello"
    }
})
```
Browser sends:

```http
OPTIONS /users HTTP/1.1
Origin: https://app.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: Authorization, X-Custom
```
Server response

```http
HTTP/1.1 204 No Content
```

#### Host

```http
Host: api.example.com
```

#### Content Type (Res)

```http
Content-Type: application/json
```

#### Content Length

```http
Content-Length: 532
```

#### User Agent

```http
User-Agent: curl/8.0
```

#### Transfer-Encoding

```http
Transfer-Encoding: chunked
```

#### Accept

```http
Accept: application/json
```

#### Connection

```http
Connection: keep-alive
Connection: close
```

#### Origin

Indicates which website initiated this request (Used in cors)
```http
Origin: https://app.com
```

#### X-Forwarded-For

Original client IP
```http
X-Forwarded-For: 1.2.3.4
```

#### X-Request-ID

Generate in nginx using:

```nginx
proxy_set_header X-Request-ID $request_id;
```

```http
X-Request-ID: abc123
```

#### Content-Encoding

The client sends `accept-encoding` in the request headers. The server responds with the chosen encoding
```http
Content-Encoding: gzip
```

#### Strict-Transport-Security

Sent by the server, the browser rewrites all http requests to https
```http
Strict-Transport-Security: max-age=31536000
```

### Authorization headers

- Cookie: Server sends set-cookie, the browser stores the  cookie and sends it for every applicable request
- Authorization: Bearer <JWT>: Browser does not automaticaally handle this, the frontend must explicitly store the token in the local storage and send it to fetch server data.

### Rate limiting headers

### Caching headers
Cache-Control
ETag
