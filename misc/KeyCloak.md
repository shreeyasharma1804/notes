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

### Create a new admin user

- In Users
- Role binding: Manage users

### Get the access token for creating a new User in realm-1

```
curl --location 'https://localhost:8443/realms/realm-1/protocol/openid-connect/token' \
--header 'Content-Type: application/x-www-form-urlencoded' \
--data-urlencode 'grant_type=password' \
--data-urlencode 'client_id=admin-cli' \
--data-urlencode 'username=shreeya-admin' \
--data-urlencode 'password=.xe7yupy)M=~,XP'
```

- The JWT access token is issued to client_id.

### User registration

- Enable user registration in realm settings
