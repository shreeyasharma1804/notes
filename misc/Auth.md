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
