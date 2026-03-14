import os

from flask import Flask, redirect, url_for, session, jsonify, render_template_string  # type: ignore[import-untyped]
from authlib.integrations.flask_client import OAuth  # type: ignore[import-untyped]

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

KEYCLOAK_BASE_URL = os.environ.get("KEYCLOAK_BASE_URL", "http://localhost:8080")
# Public URL is what the *browser* uses — must be reachable from the user's machine.
# Defaults to KEYCLOAK_BASE_URL so local runs without Docker work unchanged.
KEYCLOAK_PUBLIC_URL = os.environ.get("KEYCLOAK_PUBLIC_URL", KEYCLOAK_BASE_URL)
KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "juju")
CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "test-app")
CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "secret")

# Internal realm URL — used server-side (token exchange, metadata fetch)
REALM_URL = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
# Public realm URL — used for browser redirects (login, logout)
PUBLIC_REALM_URL = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"
SERVER_METADATA_URL = f"{REALM_URL}/.well-known/openid-configuration"

# ---------------------------------------------------------------------------
# OAuth / OIDC setup
# ---------------------------------------------------------------------------
oauth = OAuth(app)

keycloak_client = oauth.register(
    name="keycloak",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=SERVER_METADATA_URL,
    client_kwargs={
        "scope": "openid email profile",
        "token_endpoint_auth_method": "client_secret_post",
    },
)

# ---------------------------------------------------------------------------
# HTML templates (inline to keep the project self-contained)
# ---------------------------------------------------------------------------
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keycloak Test App</title>
</head>
<body>
  <h1>Keycloak OIDC Test App</h1>
  <p>Realm: <strong>{{ realm }}</strong> &mdash; Client: <strong>{{ client_id }}</strong></p>
  {% if user %}
    <p>Logged in as <strong>{{ user }}</strong></p>
    <ul>
      <li><a href="/profile">View profile / token claims</a></li>
      <li><a href="/logout">Logout</a></li>
    </ul>
  {% else %}
    <p>You are not logged in.</p>
    <a href="/login">Login via Keycloak</a>
  {% endif %}
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    user = session.get("user_info", {}).get("preferred_username")
    return render_template_string(
        HOME_TEMPLATE,
        user=user,
        realm=KEYCLOAK_REALM,
        client_id=CLIENT_ID,
    )


@app.route("/login")
def login():
    """Redirect the browser to the Keycloak login page."""
    redirect_uri = url_for("callback", _external=True)
    return keycloak_client.authorize_redirect(redirect_uri)


@app.route("/callback")
def callback():
    """Handle the OIDC redirect back from Keycloak.

    Authlib exchanges the authorisation code for tokens, validates the
    id_token, and returns the full token response.
    """
    token = keycloak_client.authorize_access_token()

    # The parsed id_token claims are stored under the 'userinfo' key by
    # Authlib when the server supports the userinfo endpoint, otherwise
    # we fall back to the id_token claims directly.
    user_info = token.get("userinfo") or {}

    session["user_info"] = dict(user_info)
    session["id_token"] = token.get("id_token")  # raw JWT, needed for logout

    return redirect(url_for("home"))


@app.route("/profile")
def profile():
    """Protected route — shows username, email, and all token claims as JSON."""
    user_info = session.get("user_info")
    if not user_info:
        return redirect(url_for("login"))

    payload = {
        "username": user_info.get("preferred_username"),
        "email": user_info.get("email"),
        "claims": user_info,
    }
    return jsonify(payload)


@app.route("/logout")
def logout():
    """Clear the local session, then redirect to the Keycloak logout endpoint.

    Keycloak's end_session_endpoint will invalidate the SSO session on the
    server side and redirect the browser back to the application root.
    """
    id_token_hint = session.pop("id_token", None)
    session.clear()

    # Build the Keycloak end-session URL.  The post_logout_redirect_uri must
    # be registered as a valid redirect URI in the Keycloak client settings.
    post_logout_redirect = url_for("home", _external=True)
    logout_url = (
        f"{PUBLIC_REALM_URL}/protocol/openid-connect/logout"
        f"?post_logout_redirect_uri={post_logout_redirect}"
        f"&client_id={CLIENT_ID}"
    )
    if id_token_hint:
        logout_url += f"&id_token_hint={id_token_hint}"

    return redirect(logout_url)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
