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

- Redirect URIs
- PKCE
- Confidential clients

### User registration/loging

- User registration should be enabled in realm settings
- If the app needs to authenticate a user, it needs to send a get request as below:

```bash
https://localhost:8443/realms/realm-1/protocol/openid-connect/auth?client_id=demo_client_id&response_type=code&redirect_uri=http://localhost:5000/callback&scope=openid

realm-1: The realm in which the user exists/ needs to be created
client_id: The app which is authenticating the user
code: The code can be used only once to generate the access token
The redirect URI: should match one of the valid redirect URIs inthe client config in keycloak
scope: 
```

- If signing in, keycloak checks that the password provided by the user is correct
- If registering, keycloak creates a new user for the realm realm-1
- After this, keyclock redirects to the provided redirect_uri with a valid code
- Generate access token, refresh token etc from this code:

```bash
curl -k -X POST 'https://localhost:8443/realms/realm-1/protocol/openid-connect/token' \
      --header 'Content-Type: application/x-www-form-urlencoded' \
      --data-urlencode 'grant_type=authorization_code' \
      --data-urlencode 'client_id=demo_client_id' \
      --data-urlencode 'code=a244e6c5-7488-7e3c-ef1a-7814e8f2edf5.UJhcPUdrTSoSroY_6Vcotd_c.976db4a3-c197-44ab-8513-70911172ac3d' \
      --data-urlencode 'redirect_uri=http://localhost:5000/callback' \
      --data-urlencode 'client_secret=zKcnH6czFuB8OzE21xRY6zNlUhGtpy9xJVjhBSbUwx42CRoJ0DxOgfeweaCbd47cM43GEraDsTlIgdqY6Iu7KN'
{

# client_secret is required only if the client is confidential
```
