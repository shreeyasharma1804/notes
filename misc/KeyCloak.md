### Setup

```
# Create the network
docker network create keycloak

# Run the DB
docker run -d \
  --name postgres \
  --network keycloak \
  -e POSTGRES_USER=myuser \
  -e POSTGRES_PASSWORD=mypassword \
  -e POSTGRES_DB=keycloak \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:17

# Run keycloack
docker run -d \
  --name mykeycloak \
  --network keycloak \
  -p 127.0.0.1:8443:8443 \
  -v /Users/shreeya/Documents/oidc/certs:/certs:ro \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=change_me \
  quay.io/keycloak/keycloak:latest \
  start \
    --hostname=localhost \
    --db=postgres \
    --db-url=jdbc:postgresql://postgres:5432/keycloak \
    --db-username=myuser \
    --db-password=mypassword \
    --https-certificate-file=/certs/certificate.crt \
    --https-certificate-key-file=/certs/private.key
```

### Create a realm

- Each realm contains users, credentials, roles etc
- Can be created from a UI
- Persisted in the DB:

```sql
SELECT id, name, enabled FROM realm;
```

### Create the client

- Redirect URIs: The valid URIs which can be sent as reidrect URIs in /auth request. The application should have endpoints listening on these URIs.
- Confidential clients: The clients which require a client_secret to generate the access token from the authorization token
- PKCE: PKCE is used to ensure that only the client_id which request the auth token can use it to generate the access token. If enabled, when redirecting to /auth, the client needs to send a code_verifier, which is a hash of a code_challege (random string). The code_verifier is stored by keycloak as the unique string bound to the authorization toke. Later, when requesting the access token to keycloak, the client sends the code_challege

### User registration/loging

- User registration should be enabled in realm settings
- If the app needs to authenticate a user, it needs to send a get request as below:

```bash
https://localhost:8443/realms/realm-1/protocol/openid-connect/auth?client_id=demo_client_id&response_type=code&redirect_uri=http://localhost:5000/callback&scope=openid

realm-1: The realm in which the user exists/ needs to be created
client_id: The app which is authenticating the user
code: The code can be used only once to generate the access token
The redirect URI: should match one of the valid redirect URIs inthe client config in keycloak
scope: The required user claims
```

- If signing in, keycloak checks that the password provided by the user is correct
- If registering, keycloak creates a new user for the realm realm-1
- After this, keyclock redirects to the provided redirect_uri with a one time authorization code (TTL ~ 60 seconds)
- Generate access token, refresh token etc from the authorization code:

```bash
curl -k -X POST 'https://localhost:8443/realms/realm-1/protocol/openid-connect/token' \
      --header 'Content-Type: application/x-www-form-urlencoded' \
      --data-urlencode 'grant_type=authorization_code' \
      --data-urlencode 'client_id=demo_client_id' \
      --data-urlencode 'code=a244e6c5-7488-7e3c-ef1a-7814e8f2edf5.UJhcPUdrTSoSroY_6Vcotd_c.976db4a3-c197-44ab-8513-70911172ac3d' \
      --data-urlencode 'redirect_uri=http://localhost:5000/callback' \
      --data-urlencode 'client_secret=zKcnH6czFuB8OzE21xRY6zNlUhGtpy9xJVjhBSbUwx42CRoJ0DxOgfeweaCbd47cM43GEraDsTlIgdqY6Iu7KN'

# client_secret is required only if the client is confidential
```

- Resposne:

```
{"access_token":"eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJDZkJNb0t3TlV1YjN3UV9yTzlZeU5od1lqTldDeTRLVzZLdFlxWDJqeHhnIn0.eyJleHAiOjE3ODQ5NzkzNjIsImlhdCI6MTc4NDk3OTA2MiwiYXV0aF90aW1lIjoxNzg0OTc4ODExLCJqdGkiOiJvbnJ0YWM6MjgyYjBlY2MtY2QzYy1kMWQ0LWYxNDEtOWYwZThlM2U0OTZiIiwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3Q6ODQ0My9yZWFsbXMvcmVhbG0tMSIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiI3Mzg3YWM4NC02MDIxLTQxNjItYjc0ZC0xNDIwNjVhOTZlZTgiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJkZW1vX2NsaWVudF9pZCIsInNpZCI6IlVKaGNQVWRyVFNvU3JvWV82VmNvdGRfYyIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiaHR0cDovL2xvY2FsaG9zdDo1MDAwIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1yZWFsbS0xIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IlNocmVleWEgU2hyZWV5YSIsInByZWZlcnJlZF91c2VybmFtZSI6ImRlbW8tdXNlciIsImdpdmVuX25hbWUiOiJTaHJlZXlhIiwiZmFtaWx5X25hbWUiOiJTaHJlZXlhIiwiZW1haWwiOiJzaHJlZXlhQGdtYWlsLmNvbSJ9.AsxrPhPemqGd2q5AG2fN0K9U8pAkaZ0LPlYiDaeHha07UmI9LRW6RZ26B9Uu4eYgZ_xoaRC1m1NSi1gXgNBm-Zn2In2r-mfwvymKWxbPBaZPbFXSGR56YruaLNY_t23g3VytOxml3m7dqERGtCV8yEmI5eOJ9a8sklBAgZGkMRiG_kWgwNVN--UMnEQWlLFaoZu7Vnc-FSX47sgmJkD_oJ2yDAUS3sg4mLbh-llcpFDo3YpPMy2YeNXmfOWfuzd8Pa97E4PsOrBms5B_VTE8ZHxgROxi6l7YQ7ym6XRsxFKjkmykY7-Q4qbH__mVv20foKenBiJ5G9M47IH0WVSLuQ","expires_in":300,"refresh_expires_in":1800,"refresh_token":"eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjODZmMmJmNy1kYTE3LTRhMGQtOTIzYy1kYjNjYzAzYmZiYzUifQ.eyJleHAiOjE3ODQ5ODA4NjIsImlhdCI6MTc4NDk3OTA2MiwianRpIjoiZmRhMDAyNDAtOWEyMi1lMzlkLTlkN2YtMGRlNWJjODQ4MzY2IiwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3Q6ODQ0My9yZWFsbXMvcmVhbG0tMSIsImF1ZCI6Imh0dHBzOi8vbG9jYWxob3N0Ojg0NDMvcmVhbG1zL3JlYWxtLTEiLCJzdWIiOiI3Mzg3YWM4NC02MDIxLTQxNjItYjc0ZC0xNDIwNjVhOTZlZTgiLCJ0eXAiOiJSZWZyZXNoIiwiYXpwIjoiZGVtb19jbGllbnRfaWQiLCJzaWQiOiJVSmhjUFVkclRTb1Nyb1lfNlZjb3RkX2MiLCJzY29wZSI6Im9wZW5pZCBlbWFpbCBzZXJ2aWNlX2FjY291bnQgd2ViLW9yaWdpbnMgYWNyIHByb2ZpbGUgYmFzaWMgcm9sZXMiLCJhdWRfeCI6ImFjY291bnQiLCJwcm92IjoiZGVmYXVsdCJ9.ydAEK6OE3y90Y7teKJY8T6-z37tSvaa2LQeFrq5OSg6JcxVFwLumrjONxZ5kyC4NxW4roP85EsEcoeL1aM8XdQ","token_type":"Bearer","id_token":"eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJDZkJNb0t3TlV1YjN3UV9yTzlZeU5od1lqTldDeTRLVzZLdFlxWDJqeHhnIn0.eyJleHAiOjE3ODQ5NzkzNjIsImlhdCI6MTc4NDk3OTA2MiwiYXV0aF90aW1lIjoxNzg0OTc4ODExLCJqdGkiOiIzNTZlNmEwMC0wYTY1LTMwMzEtNGYyZS1mMzNhZWFmOWYwMWQiLCJpc3MiOiJodHRwczovL2xvY2FsaG9zdDo4NDQzL3JlYWxtcy9yZWFsbS0xIiwiYXVkIjoiZGVtb19jbGllbnRfaWQiLCJzdWIiOiI3Mzg3YWM4NC02MDIxLTQxNjItYjc0ZC0xNDIwNjVhOTZlZTgiLCJ0eXAiOiJJRCIsImF6cCI6ImRlbW9fY2xpZW50X2lkIiwic2lkIjoiVUpoY1BVZHJUU29Tcm9ZXzZWY290ZF9jIiwiYXRfaGFzaCI6IlBSdDVsbV9tNGNaNVpIM3B5NmxHMkEiLCJhY3IiOiIwIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJuYW1lIjoiU2hyZWV5YSBTaHJlZXlhIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiZGVtby11c2VyIiwiZ2l2ZW5fbmFtZSI6IlNocmVleWEiLCJmYW1pbHlfbmFtZSI6IlNocmVleWEiLCJlbWFpbCI6InNocmVleWFAZ21haWwuY29tIn0.QwXJJDqHdHKKVfBU_UHDZtMoFA9UXvUFnVeZ8HpvWtck5TwTKoePi7xWTdgX9wnr3s8CyycaNoA-Z0g6nhr-AVFihjzZcEa5hU5YT9_PFcjRFBBoUXavvEy8j3DGeJt3ALxqdlLFBRK7RvGkSQbOSudvWfeAJI4W8nh2ZHjEe2e1_qrsUbzxev0bPZqPbbo6YYX4gj4bBN6tJFPFo3VojJ8dO9yNSBL5Of8ZboMoLAwaeWGCHDBqBKDyrMF32H12ooQKAtC7qaBfxppAvkIuQqPW4D6lJVNU29pTgsEWIdXtBhom0gkkfF1W8Kp5DuNrK65wU0gvf6x5S0_uYSCcrQ","not-before-policy":0,"session_state":"UJhcPUdrTSoSroY_6Vcotd_c","scope":"openid email profile"}⏎
```

- The TTLs of authorization code, access token and refresh token are configurable via keycloak

#### Access token:
- iss: https://localhost:8443/realms/realm-1
- sub: The client_id of the user logged in (How to change sub)
- azp: The client_id which is authorized to generate the acess tokens

#### Refresh token:
- iss: https://localhost:8443/realms/realm-1
- type: refresh

#### ID Token
- Contains all the user info required as per the scope

#### Get access token from refresh token

```
curl -k -X POST 'https://localhost:8443/realms/realm-1/protocol/openid-connect/token' \
      --header 'Content-Type: application/x-www-form-urlencoded' \
      --data-urlencode 'grant_type=refresh_token' \
      --data-urlencode 'client_id=demo_client_id' \
      --data-urlencode 'refresh_token=eyJhbGciOiJIUzUxMiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjODZmMmJmNy1kYTE3LTRhMGQtOTIzYy1kYjNjYzAzYmZiYzUifQ.eyJleHAiOjE3ODUwNzU3MzEsImlhdCI6MTc4NTA3MzkzMSwianRpIjoiOGEwNzJiNzMtZGE4Ni0zN2Y3LTFlNTUtZTdlNjg3M2Q5ZDU3IiwiaXNzIjoiaHR0cHM6Ly9sb2NhbGhvc3Q6ODQ0My9yZWFsbXMvcmVhbG0tMSIsImF1ZCI6Imh0dHBzOi8vbG9jYWxob3N0Ojg0NDMvcmVhbG1zL3JlYWxtLTEiLCJzdWIiOiI3Mzg3YWM4NC02MDIxLTQxNjItYjc0ZC0xNDIwNjVhOTZlZTgiLCJ0eXAiOiJSZWZyZXNoIiwiYXpwIjoiZGVtb19jbGllbnRfaWQiLCJzaWQiOiJTQWlKWjlxbHc5VzdVQ2RMTmEycWNJUXEiLCJzY29wZSI6Im9wZW5pZCBlbWFpbCBzZXJ2aWNlX2FjY291bnQgd2ViLW9yaWdpbnMgYWNyIHByb2ZpbGUgYmFzaWMgcm9sZXMiLCJhdWRfeCI6ImFjY291bnQiLCJwcm92IjoiZGVmYXVsdCJ9.F0IxmxvwAvarJFSQyGL233KUmxnMNsqZzDtjwDxp7icO8JM8tgnzbvx522E-Lw2QhXhfk16cSMCh-JPuFiGUJA' \
      --data-urlencode 'client_secret=zKcnH6czFuB8OzE21xRY6zNlUhGtpy9xJVjhBSbUwx42CRoJ0DxOgfeweaCbd47cM43GEraDsTlIgdqY6Iu7KN'
```

### Service accounts

- A service account is automatically created for a client if it is:
  - Confidential
  - Service account roles is enabled
 
<img width="830" height="495" alt="image" src="https://github.com/user-attachments/assets/d30ceb85-d46e-405f-9de7-0b3517a43e6c" />

- To get an access token, we just need to call the /token endpoint with the client_id and secret
- The subject of the token is the system accountuser id

```bash
curl -k -X POST 'https://localhost:8443/realms/realm-1/protocol/openid-connect/token' \
            --header 'Content-Type: application/x-www-form-urlencoded' \
            --data-urlencode 'grant_type=client_credentials' \
            --data-urlencode 'client_id=demo_client_id' \
            --data-urlencode 'client_secret=zKcnH6czFuB8OzE21xRY6zNlUhGtpy9xJVjhBSbUwx42CRoJ0DxOgfeweaCbd47cM43GEraDsTlIgdqY6Iu7KN'
```

### Multiple Audiences

- JWT token validation by an applications checks that whether the token was generated for it through the aud field in the JWT token

```
Client -> Client scopes -> <client_id>-dedicated -> Configure new mapper -> Audience
```

- The audience needs to be mapped to an actual client_id. Then, the mapped client_id will appear in the access tokens generated for this application.
- This feature is used when an application authenticates a user through JWT, and not via redirectingthe user to keycloak. (Token exchnage)

### RBAC and Groups

- Groups: Add the user to a group, to include in JWT:

```bash
Clients -> Client Scopes -> <client-id>_dedicated -> Add mapper -> By configuration -> Group membership
```

- Roles: Clients -> Roles -> Create Role, Users -> Role Mapping -> Assign Role

### Middleware

- Check if JWT is not expired
- Verify that the signature is valid
- Check the user in the sub
- Check the role
- Check if the user is mapped to the required groups
- Check the aud (if token exchange is used)


### Authorization

- Create a new role in the client
- Assign a role to a user
- The role is defined under resource_access in the access token
```
{
  "demo_client_id": {
    "roles": [
      "app_users"
    ]
  }
```

### 
