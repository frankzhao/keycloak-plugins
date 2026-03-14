# test-app

A minimal Flask application that authenticates users via Keycloak using the OIDC Authorization Code flow. Used to verify the custom login and mapper SPIs end-to-end.

## Routes

| Route | Auth required | Description |
|-------|---------------|-------------|
| `GET /` | No | Home page — shows login link or logged-in username |
| `GET /login` | No | Redirects to Keycloak login (triggers the justification form) |
| `GET /callback` | No | OIDC redirect handler — exchanges code for tokens |
| `GET /profile` | Yes | Displays username, email, and all token claims as JSON |
| `GET /logout` | No | Clears session and redirects to Keycloak's end-session endpoint |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KEYCLOAK_BASE_URL` | `http://localhost:8080` | Internal Keycloak URL (server-side token exchange) |
| `KEYCLOAK_PUBLIC_URL` | same as `KEYCLOAK_BASE_URL` | Browser-facing Keycloak URL (authorization redirect) |
| `KEYCLOAK_REALM` | `juju` | Realm name |
| `KEYCLOAK_CLIENT_ID` | `test-app` | OIDC client ID |
| `KEYCLOAK_CLIENT_SECRET` | `secret` | Client secret (Clients → test-app → Credentials) |
| `SECRET_KEY` | `dev-secret` | Flask session signing key |
| `PORT` | `5000` | Port the server listens on |
| `FLASK_DEBUG` | `true` | Enable Flask debug mode |

`KEYCLOAK_PUBLIC_URL` only needs to differ from `KEYCLOAK_BASE_URL` when running inside Docker, where the internal hostname (`keycloak:8080`) is not reachable from the browser.

## Running locally

```sh
cd test-app
cp .env.example .env          # edit as needed
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py                 # http://localhost:5000
```

## Running via Docker Compose

```sh
docker compose up --build
# http://localhost:5001
```

## Keycloak prerequisites

The `juju` realm must have a `test-app` client configured before the app will work. See the root [README](../README.md) for full setup instructions, including:

- Creating the `juju` realm
- Creating the `test-app` client with correct redirect URIs
- Wiring the justification authenticator into the browser flow
- Adding the username suffix mapper to the client scope
