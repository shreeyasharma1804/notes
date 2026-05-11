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
