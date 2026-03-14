#!/usr/bin/env python3
"""
Idempotent setup script for the juju realm.

Configures:
  - juju realm
  - test-app OIDC client (secret: "secret", redirect: http://localhost:5001/*)
  - browser-with-justification auth flow (browser flow + justification form step)
  - username suffix mapper on test-app (@example.com -> preferred_username)
  - saml-test SAML Identity Provider (metadata imported from test SAML IdP)
  - username transform mapper on the SAML IdP (${username}-foo)

Safe to run multiple times — each step checks whether it already exists.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any  # noqa: F401 — used in type annotations

KEYCLOAK_URL = "http://keycloak:8080"
SAML_IDP_URL = "http://saml-idp:8080"
REALM        = "juju"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _do(method: str, path: str, data: Any = None, token: str | None = None, base: str = KEYCLOAK_URL) -> Any:
    url     = f"{base}{path}"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req  = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} → {exc.code}: {exc.read().decode()}") from exc


def get(path: str, token: str) -> Any:
    return _do("GET", path, token=token)

def post(path: str, data: Any, token: str) -> Any:
    return _do("POST", path, data=data, token=token)

def put(path: str, data: Any, token: str) -> Any:
    return _do("PUT", path, data=data, token=token)

def delete(path: str, token: str) -> None:
    _do("DELETE", path, token=token)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_token():
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id":  "admin-cli",
        "username":   "admin",
        "password":   "admin",
    }).encode()
    req = urllib.request.Request(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


# ---------------------------------------------------------------------------
# Readiness polling
# ---------------------------------------------------------------------------

def wait_for(label, url, retries=60, delay=3):
    print(f"Waiting for {label}...", flush=True)
    for _ in range(retries):
        try:
            urllib.request.urlopen(url)
            print(f"{label} is ready.", flush=True)
            return
        except Exception:
            time.sleep(delay)
    raise RuntimeError(f"{label} did not become ready after {retries * delay}s")


# ---------------------------------------------------------------------------
# Setup steps
# ---------------------------------------------------------------------------

def setup_realm(token):
    try:
        get(f"/admin/realms/{REALM}", token)
        print(f"  realm '{REALM}' already exists")
        return token
    except RuntimeError:
        pass
    print(f"  creating realm '{REALM}'...")
    post("/admin/realms", {"realm": REALM, "enabled": True}, token)
    return get_token()  # refresh after realm creation


def get_client_uuid(token):
    clients = get(f"/admin/realms/{REALM}/clients?clientId=test-app", token)
    return clients[0]["id"] if clients else None


def setup_client(token):
    if get_client_uuid(token):
        print("  client 'test-app' already exists")
        return
    print("  creating client 'test-app'...")
    post(f"/admin/realms/{REALM}/clients", {
        "clientId":              "test-app",
        "enabled":               True,
        "clientAuthenticatorType": "client-secret",
        "secret":                "secret",
        "redirectUris":          ["http://localhost:5001/*"],
        "attributes":            {"post.logout.redirect.uris": "http://localhost:5001/*"},
        "standardFlowEnabled":   True,
        "publicClient":          False,
    }, token)


def setup_suffix_mapper(token):
    cid      = get_client_uuid(token)
    mappers  = get(f"/admin/realms/{REALM}/clients/{cid}/protocol-mappers/models", token)
    if any(m["name"] == "suffix mapper" for m in mappers):
        print("  suffix mapper already exists")
        return
    print("  adding username suffix mapper...")
    post(f"/admin/realms/{REALM}/clients/{cid}/protocol-mappers/models", {
        "name":            "suffix mapper",
        "protocol":        "openid-connect",
        "protocolMapper":  "username-suffix-mapper",
        "consentRequired": False,
        "config": {
            "username.suffix":     "@example.com",
            "claim.name":          "preferred_username",
            "id.token.claim":      "true",
            "access.token.claim":  "true",
            "userinfo.token.claim":"true",
        },
    }, token)


def _add_justification_to_flow(flow_alias, token):
    """Add the justification step to the top level of a flow and set it REQUIRED."""
    post(
        f"/admin/realms/{REALM}/authentication/flows/{urllib.parse.quote(flow_alias)}/executions/execution",
        {"provider": "justification-authenticator"},
        token,
    )
    executions = get(
        f"/admin/realms/{REALM}/authentication/flows/{urllib.parse.quote(flow_alias)}/executions",
        token,
    )
    just_exec = next(e for e in executions if e.get("providerId") == "justification-authenticator")
    just_exec["requirement"] = "REQUIRED"
    put(
        f"/admin/realms/{REALM}/authentication/flows/{urllib.parse.quote(flow_alias)}/executions",
        just_exec,
        token,
    )


def setup_auth_flow(token):
    """Browser flow for local logins: copy browser flow and add justification
    inside the Browser Forms subflow (after username/password + OTP)."""
    flows = get(f"/admin/realms/{REALM}/authentication/flows", token)
    existing = next((f for f in flows if f["alias"] == "browser-with-justification"), None)

    need_add_step = False

    if existing:
        executions = get(
            f"/admin/realms/{REALM}/authentication/flows/browser-with-justification/executions",
            token,
        )
        just_execs = [e for e in executions if e.get("providerId") == "justification-authenticator"]
        if not just_execs:
            print("  justification step missing — will add it...")
            need_add_step = True
        else:
            print("  auth flow already correct")

    if not existing:
        print("  copying browser flow...")
        post(
            f"/admin/realms/{REALM}/authentication/flows/browser/copy",
            {"newName": "browser-with-justification"},
            token,
        )
        need_add_step = True

    if need_add_step:
        executions = get(
            f"/admin/realms/{REALM}/authentication/flows/browser-with-justification/executions",
            token,
        )
        browser_forms = next(
            e for e in executions
            if e.get("authenticationFlow") and "forms" in e.get("displayName", "").lower()
        )
        subflow_alias = browser_forms["displayName"]
        print("  adding justification step inside browser forms subflow...")
        _add_justification_to_flow(subflow_alias, token)
        print("  justification step added and set to REQUIRED")

    realm_data = get(f"/admin/realms/{REALM}", token)
    if realm_data.get("browserFlow") != "browser-with-justification":
        print("  binding flow to realm...")
        realm_data["browserFlow"] = "browser-with-justification"
        put(f"/admin/realms/{REALM}", realm_data, token)
    else:
        print("  flow already bound")


def setup_post_broker_flow(token):
    """Post broker login flow for federated (SAML/OIDC) logins: a minimal flow
    containing only the justification step, bound to the saml-test IdP."""
    FLOW_ALIAS = "post-broker-justification"

    flows = get(f"/admin/realms/{REALM}/authentication/flows", token)
    existing = next((f for f in flows if f["alias"] == FLOW_ALIAS), None)

    if existing:
        executions = get(
            f"/admin/realms/{REALM}/authentication/flows/{urllib.parse.quote(FLOW_ALIAS)}/executions",
            token,
        )
        if any(e.get("providerId") == "justification-authenticator" for e in executions):
            print("  post-broker flow already correct")
        else:
            print("  adding justification step to post-broker flow...")
            _add_justification_to_flow(FLOW_ALIAS, token)
            print("  justification step added")
    else:
        print("  creating post-broker-justification flow...")
        post(f"/admin/realms/{REALM}/authentication/flows", {
            "alias":       FLOW_ALIAS,
            "description": "Runs justification form after any IdP login",
            "providerId":  "basic-flow",
            "topLevel":    True,
            "builtIn":     False,
        }, token)
        _add_justification_to_flow(FLOW_ALIAS, token)
        print("  post-broker flow created with justification step")

    # Bind the flow to the SAML IdP
    idp = get(f"/admin/realms/{REALM}/identity-provider/instances/saml-test", token)
    if idp.get("postBrokerLoginFlowAlias") == FLOW_ALIAS:
        print("  post-broker flow already bound to saml-test IdP")
    else:
        print("  binding post-broker flow to saml-test IdP...")
        idp["postBrokerLoginFlowAlias"] = FLOW_ALIAS
        put(f"/admin/realms/{REALM}/identity-provider/instances/saml-test", idp, token)


def setup_saml_idp(token):
    SAML_IDP_PUBLIC_URL = "http://localhost:8085"

    try:
        existing_idp = get(f"/admin/realms/{REALM}/identity-provider/instances/saml-test", token)
        cfg = existing_idp.get("config", {})
        dirty = False
        # Repair SSO URLs if they still point to the internal hostname
        if any(SAML_IDP_URL in str(v) for v in cfg.values()):
            print("  patching SAML IdP SSO URLs to public hostname...")
            for key, val in cfg.items():
                if isinstance(val, str) and SAML_IDP_URL in val:
                    cfg[key] = val.replace(SAML_IDP_URL, SAML_IDP_PUBLIC_URL)
            dirty = True
        # Repair principalAttribute if it was set to 'uid' (numeric) instead of 'cn'
        if cfg.get("principalAttribute") == "uid":
            print("  patching SAML IdP principalAttribute uid -> cn...")
            cfg["principalAttribute"] = "cn"
            dirty = True
        if dirty:
            put(f"/admin/realms/{REALM}/identity-provider/instances/saml-test", existing_idp, token)
        else:
            print("  SAML IdP already exists")
    except RuntimeError:
        print("  importing SAML metadata...")
        idp_config = post(
            f"/admin/realms/{REALM}/identity-provider/import-config",
            {
                "fromUrl":    f"{SAML_IDP_URL}/simplesaml/saml2/idp/metadata.php",
                "providerId": "saml",
            },
            token,
        )
        # The test IdP uses transient NameIDs; use the 'cn' SAML attribute
        # as the principal (username). 'uid' is a numeric ID (1, 2, ...), while
        # 'cn' contains the actual username (user1, user2, ...).
        idp_config["principalType"]      = "ATTRIBUTE"
        idp_config["principalAttribute"] = "cn"

        # Metadata was fetched from the internal Docker hostname (saml-idp:8080).
        # Rewrite SSO/SLO endpoint URLs to the public hostname so the browser
        # can reach the IdP when Keycloak redirects the user there.
        for key, val in idp_config.items():
            if isinstance(val, str) and SAML_IDP_URL in val:
                idp_config[key] = val.replace(SAML_IDP_URL, SAML_IDP_PUBLIC_URL)

        print("  creating SAML IdP...")
        post(f"/admin/realms/{REALM}/identity-provider/instances", {
            "alias":       "saml-test",
            "displayName": "Test SAML IdP",
            "providerId":  "saml",
            "enabled":     True,
            "config":      idp_config,
        }, token)

    mappers = get(
        f"/admin/realms/{REALM}/identity-provider/instances/saml-test/mappers", token
    )
    idp_mappers = [
        {
            "name":                   "username-transform",
            "identityProviderMapper": "username-transform-mapper",
            "config": {"username.template": "${username}-foo"},
        },
        {
            "name":                   "first-name",
            "identityProviderMapper": "saml-user-attribute-idp-mapper",
            "config": {"attribute.name": "givenName", "user.attribute": "firstName",
                       "syncMode": "INHERIT"},
        },
        {
            "name":                   "last-name",
            "identityProviderMapper": "saml-user-attribute-idp-mapper",
            "config": {"attribute.name": "sn", "user.attribute": "lastName",
                       "syncMode": "INHERIT"},
        },
        {
            "name":                   "email",
            "identityProviderMapper": "saml-user-attribute-idp-mapper",
            "config": {"attribute.name": "mail", "user.attribute": "email",
                       "syncMode": "INHERIT"},
        },
    ]
    existing_by_name = {m["name"]: m for m in mappers}
    for m in idp_mappers:
        if m["name"] in existing_by_name:
            existing = existing_by_name[m["name"]]
            # Update config in place to fix any wrong attribute.name
            existing["config"].update(m["config"])
            put(
                f"/admin/realms/{REALM}/identity-provider/instances/saml-test/mappers/{existing['id']}",
                existing,
                token,
            )
            print(f"  IdP mapper '{m['name']}' updated")
        else:
            print(f"  adding IdP mapper '{m['name']}'...")
            post(
                f"/admin/realms/{REALM}/identity-provider/instances/saml-test/mappers",
                {"identityProviderAlias": "saml-test", **m},
                token,
            )


def setup_required_actions(token):
    """Disable required actions that would interrupt the login flow."""
    actions = get(f"/admin/realms/{REALM}/authentication/required-actions", token)
    for action in actions:
        if action.get("alias") == "VERIFY_PROFILE" and action.get("enabled"):
            print("  disabling VERIFY_PROFILE required action...")
            action["enabled"] = False
            put(
                f"/admin/realms/{REALM}/authentication/required-actions/VERIFY_PROFILE",
                action,
                token,
            )
            return
    print("  VERIFY_PROFILE already disabled")


def setup_first_broker_login(token):
    """Disable the 'Review Profile' step so users aren't prompted to update
    their account info on every first SAML login."""
    executions = get(
        f"/admin/realms/{REALM}/authentication/flows/first%20broker%20login/executions",
        token,
    )
    review = next(
        (e for e in executions if e.get("providerId") == "idp-review-profile"),
        None,
    )
    if review is None:
        print("  review-profile step not found")
        return
    if review.get("requirement") == "DISABLED":
        print("  review-profile already disabled")
        return
    print("  disabling review-profile step in first broker login flow...")
    review["requirement"] = "DISABLED"
    put(
        f"/admin/realms/{REALM}/authentication/flows/first%20broker%20login/executions",
        review,
        token,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    wait_for("Keycloak",  f"{KEYCLOAK_URL}/health/ready")
    wait_for("SAML IdP",  f"{SAML_IDP_URL}/simplesaml/saml2/idp/metadata.php")

    token = get_token()

    steps = [
        ("realm",                setup_realm),
        ("client",               setup_client),
        ("suffix mapper",        setup_suffix_mapper),
        ("auth flow",            setup_auth_flow),
        ("SAML IdP",             setup_saml_idp),
        ("post broker flow",     setup_post_broker_flow),
        ("required actions",     setup_required_actions),
        ("first broker login",   setup_first_broker_login),
    ]

    for name, fn in steps:
        print(f"\n[{name}]", flush=True)
        result = fn(token)
        if result:
            token = result  # setup_realm returns a refreshed token

    print("\nSetup complete.", flush=True)
