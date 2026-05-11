### Cookies

Cookies are key value pairs.

```
Browser ──> login credentials ──> Server
Browser <── Set-Cookie: session=abc123 <── Server

Later:

Browser ──> Cookie: session=abc123 ──> Server
```
- httpOnly: Does not allow js to read the cookie (cannot access cookie via document.cookie)
- samesite:
    - Strict: No cookies are sent 
