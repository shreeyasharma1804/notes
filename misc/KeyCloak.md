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

### Create the client with valid redirect URIs

### Redirect to below for user registration/loging

- Enable user registration in realm settings
- Redirect from app to:

```
https://localhost:8443/realms/realm-1/protocol/openid-connect/auth?client_id=demo_client_id&response_type=code&redirect_uri=http://localhost:5000/callback&scope=openid
```
- If signing in, keycloak checks that the password provided by the user is correct
- If registering, keycloak creates a new user for the realm realm1
