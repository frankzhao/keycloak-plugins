# Keycloak Plugins

This repository demonstrates how to extend Keycloak 24 with custom Java SPIs. It contains three example plugins:

- **keycloak-custom-login** — an Authenticator SPI that adds a justification form to the browser login flow. After a user authenticates with their username and password, they are prompted to provide a justification and reason for access. The response is persisted to PostgreSQL alongside the username, timestamp, and redirect URL.

- **keycloak-custom-mapper** — a Protocol Mapper SPI that appends a configurable suffix to the username in issued tokens (e.g. `frank` → `frank@example.com`). The stored user record in Keycloak is not modified; the transformation is applied at token issuance time only.

- **keycloak-custom-idp-mapper** — an Identity Provider Mapper SPI that transforms incoming usernames from an external IdP before Keycloak looks up or creates the local user. The transformation is driven by a configurable template (e.g. `${username}-foo` maps `alice` → `alice-foo`). Compatible with any IdP type (SAML, OIDC, social).

A minimal Flask test app is included to exercise the plugins end-to-end via the OIDC Authorization Code flow. A test SAML IdP is included for testing the IdP mapper.

---

## Services

| Service      | URL                                                                 |
|--------------|---------------------------------------------------------------------|
| Keycloak     | http://localhost:8080                                               |
| Test App     | http://localhost:5001                                               |
| SAML IdP     | http://localhost:8085/simplesaml                                    |
| IdP metadata | http://localhost:8085/simplesaml/saml2/idp/metadata.php             |

Admin credentials: `admin` / `admin`

SAML IdP test users:

| Username | Password    |
|----------|-------------|
| `user1`  | `user1pass` |
| `user2`  | `user2pass` |

---

## Quick start

```sh
docker compose up --build
```

The `setup` service runs automatically after Keycloak is healthy and fully configures the `juju` realm. No manual steps are required.

To re-run setup at any time:

```sh
docker compose restart setup && docker compose logs -f setup
```

---

## What the setup script configures

The `setup` service (`scripts/setup.py`) runs once after Keycloak is healthy and performs the following steps idempotently:

| Step | What it does |
|------|-------------|
| **Realm** | Creates the `juju` realm |
| **Client** | Creates the `test-app` OIDC client (secret: `secret`, redirect: `http://localhost:5001/*`) |
| **Suffix mapper** | Adds the `username-suffix-mapper` to `test-app`, appending `@example.com` to `preferred_username` in issued tokens |
| **Auth flow** | Copies the built-in `browser` flow to `browser-with-justification`, adds the **Login Justification Form** step inside the `Browser Forms` subflow (set to **Required**), and binds it as the realm browser flow |
| **SAML IdP** | Imports the test SAML IdP metadata, sets `cn` as the principal attribute, and rewrites internal hostnames to `localhost:8085` so the browser can reach the IdP |
| **SAML mappers** | Adds the **Username Transform Mapper** (`${username}-foo`) and attribute importers for `givenName` → `firstName`, `sn` → `lastName`, `mail` → `email` |
| **Post broker flow** | Creates a `post-broker-justification` flow containing only the **Login Justification Form** step and binds it as the **Post Broker Login** flow on the `saml-test` IdP, ensuring the justification prompt appears after SAML authentication |
| **Required actions** | Disables the `VERIFY_PROFILE` required action so federated users are not prompted to complete their profile on first login |
| **First broker login** | Disables the **Review Profile** step in the first broker login flow so users are not prompted to update their account after SAML authentication |

---

## Testing the justification form

1. Create a local user in the `juju` realm (**Users** → **Add user** → set a username and password)
2. Visit http://localhost:5001/login and sign in with that user
3. After entering credentials, you will be prompted for a justification and reason
4. On success, visit http://localhost:5001/profile — `username` will show the suffixed value (e.g. `alice@example.com`)

### Verify justification records

```sh
docker compose exec postgres psql -U keycloak -c \
  "SELECT id, username, justification, reason, redirect_url, created_at FROM login_justifications;"
```

---

## Testing the SAML IdP flow

1. Visit http://localhost:5001/login
2. On the Keycloak login page, click **Test SAML IdP**
3. Log in as `user1` / `user1pass`
4. Complete the justification form
5. Visit http://localhost:5001/profile — the username will be `user1-foo`

---

## Testing the username suffix mapper

To inspect the raw token claims:

```sh
# Decode the access token (requires jq)
curl -s -X POST http://localhost:8080/realms/juju/protocol/openid-connect/token \
  -d "grant_type=password&client_id=test-app&client_secret=secret&username=<user>&password=<pass>" \
  | jq -r '.access_token' \
  | cut -d. -f2 \
  | base64 -d 2>/dev/null \
  | jq .preferred_username
```

---

## Adding the suffix mapper to a different client

The mapper is pre-configured on `test-app` by the setup script. To add it to another client manually:

1. In the `juju` realm, go to **Clients** → select the client → **Client scopes** tab
2. Click the dedicated scope link
3. Click **Add mapper** → **By configuration** → **Username Suffix Mapper**
4. Configure:
   - **Username suffix**: the string to append, e.g. `@example.com`
   - **Claim name**: `preferred_username` to override the standard claim, or a custom name
   - Enable **Add to ID token**, **Add to access token**, **Add to userinfo** as needed
5. **Save**
