### Cookies

Cookies are key value pairs.

```
Browser ──> login credentials ──> Server
Browser <── Set-Cookie: session=abc123 <── Server

Later:

Browser ──> Cookie: session=abc123 ──> Server
```
- httpOnly: Does not allow js to read the cookie (cannot access cookie via document.cookie)
- SameSite:
    - Strict: No cookies are sent.
    - Lax: blocked on most cross-site POST requests, allowed on top-level navigation GETs
    - None: Allowed everywhere
- Expires, Maxage: Expiry date of the cookie. The cookie is deleted by the browser after the expiry. The server uses seperate session key expiry to avoid expiry date manipulation of the client side.
- Domain: All the domains to which a cookie is sent.
- Path: Example, for path /api, the cookie will be only sent for the requets to /api
- Secure: If true, the cookie is only sent for https requets 

```python
from flask import Flask, request, redirect, make_response
import sqlite3
import secrets

app = Flask(__name__)

DB_NAME = "users.db"

# In-memory session store
sessions = {}

# -----------------------------
# Database setup
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Create a demo user
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password)
        VALUES (?, ?)
    """, ("admin", "password123"))

    conn.commit()
    conn.close()


# -----------------------------
# Check credentials
# -----------------------------
def validate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username=? AND password=?
    """, (username, password))

    user = cursor.fetchone()

    conn.close()

    return user is not None


# -----------------------------
# Home route
# -----------------------------
@app.route("/")
def home():
    session_id = request.cookies.get("session_id")

    if session_id in sessions:
        username = sessions[session_id]
        return f"Hello {username}"

    return """
        <h2>Login</h2>
        <form method="POST" action="/login">
            Username: <input name="username"><br><br>
            Password: <input name="password" type="password"><br><br>
            <button type="submit">Login</button>
        </form>
    """


# -----------------------------
# Login route
# -----------------------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    if not validate_user(username, password):
        return "Invalid username or password", 401

    # Create session
    session_id = secrets.token_hex(32)

    sessions[session_id] = username

    response = make_response(
        redirect("/")
    )

    # Set cookie
    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        samesite="Lax",
        secure=True
    )

    return response


# -----------------------------
# Logout route
# -----------------------------
@app.route("/logout")
def logout():
    session_id = request.cookies.get("session_id")

    if session_id in sessions:
        del sessions[session_id]

    response = make_response("Logged out")

    response.set_cookie("session_id", "", expires=0)

    return response


# -----------------------------
# Start server
# -----------------------------
if __name__ == "__main__":
    init_db()

    app.run(host="0.0.0.0", port=5000, debug=True)
```

### JWT

```
User submits username + password
Server verifies the password, creates a JWT and signs it
Server returns the token to client
The token sent by the client in all subsequent requests
```

JWT consists of:

```bash
base64url(header).base64url(payload).base64url(signature)
```
- Header: Contains the algorithm used for signing the data
- Payload: The claims of the JWT and the expiry date
- Signature

```bash
HMAC(
  base64(header) + "." + base64(payload),
  secret_key
)
```

JWT acts like a temporary signed prrof that "This client has already been authenticated by me recently."
This method is preferred over session_ids because no DB lookup is required

```python
import sqlite3
import datetime
import bcrypt
import jwt

from flask import Flask, request, jsonify, g

app = Flask(__name__)

SECRET_KEY = "super-secret-key"
DB_NAME = "users.db"

# -----------------------------
# Initialize database
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash BLOB
        )
    """)

    username = "admin"
    password = "password123"

    hashed = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (username, password_hash)
        VALUES (?, ?)
    """, (username, hashed))

    conn.commit()
    conn.close()


# -----------------------------
# Validate credentials
# -----------------------------
def validate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password_hash
        FROM users
        WHERE username = ?
    """, (username,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return False

    stored_hash = row[0]

    return bcrypt.checkpw(
        password.encode(),
        stored_hash
    )


# -----------------------------
# Middleware
# -----------------------------
@app.before_request
def authenticate():
    # Skip auth for login route
    if request.path == "/login":
        return

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({
            "error": "Missing token"
        }), 401

    try:
        token = auth_header.split(" ")[1]

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        # Store user info globally for request
        g.user = payload

    except jwt.ExpiredSignatureError:
        return jsonify({
            "error": "Token expired"
        }), 401

    except jwt.InvalidTokenError:
        return jsonify({
            "error": "Invalid token"
        }), 401


# -----------------------------
# Login endpoint
# -----------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data.get("username")
    password = data.get("password")

    if not validate_user(username, password):
        return jsonify({
            "error": "Invalid credentials"
        }), 401

    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow()
               + datetime.timedelta(hours=1)
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Login successful",
        "jwt": token
    })


# -----------------------------
# Protected route
# -----------------------------
@app.route("/profile")
def profile():
    return jsonify({
        "message": "Authenticated",
        "user": g.user["username"]
    })


# -----------------------------
# Start app
# -----------------------------
if __name__ == "__main__":
    init_db()

    app.run(debug=True)
```

### OIDC

- Client sends request to the host (goes via nginx) along with the cookies (contains a session_id for the host)
- Nginx checks if the session_id is stored in redis.
- If the session_id is not valid, nginx sends a redirect response 302 with the location as the uri of the identity management url and a redirect_uri. 
- Browser sends a request to the identity management url
- identity management fetches the user info (...somehow) and sends a redirect response with the location as the original host url. It also adds a session_id and a one time code to this redirect url
- Browser recieves this redirect url and sends it to nginx again
- With the valid code, nginx sends a request to the identity management url
- identity management returns id_token, access_token and refresh_token
- Based on the user info in the id_token, LDAP calls can be made to check if the user can access the upstream applicaton. If not "401" Not authorized is returned.
- The access_token is passed to the upstream app by nginx via Authorization header
- Upstream apps have middlewares which check the validity of the access token before returning any resource.
- id_token and access_token server different purposes in terms of authentication and authorization
- access_token can be refreshed using the refresh token
- The user does not store any sensitive tokens, which removes the possibility of the token getting stolen. All tokens are stored in redis.
