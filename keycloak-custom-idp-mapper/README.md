# keycloak-custom-idp-mapper

A Keycloak Identity Provider Mapper SPI that applies a configurable transformation rule to the incoming username before Keycloak looks up or creates the corresponding local user.

This is useful when the username asserted by an external IdP (e.g. a SAML provider) does not match the format used in Keycloak. The transformation is applied at federation time — the stored Keycloak user record reflects the transformed username, not the original asserted value.

## How it works

When a user authenticates through an external Identity Provider, Keycloak calls `preprocessFederatedIdentity` before attempting to find or create a local user. This mapper intercepts that call, applies the configured template to the incoming username, and sets the result as the local username.

On subsequent logins, `updateBrokeredUser` ensures the local username stays in sync with the rule.

## Provider

| SPI | ID | Class |
|-----|----|-------|
| IdentityProviderMapper | `username-transform-mapper` | `UsernameTransformMapper` |

Compatible with any Identity Provider (SAML, OIDC, social logins, etc.).

## Configuration

| Field | Default | Description |
|-------|---------|-------------|
| **Username template** | `${username}` | Transformation rule. Use `${username}` as a placeholder for the incoming username. |

### Template examples

| Template | Incoming username | Result |
|----------|-------------------|--------|
| `${username}-foo` | `alice` | `alice-foo` |
| `${username}` | `alice` | `alice` (no change) |
| `${username}@corp` | `alice` | `alice@corp` |
| `svc-${username}` | `alice` | `svc-alice` |

## Wiring up the mapper

1. In the target realm, go to **Identity Providers** → select your IdP
2. Open the **Mappers** tab → **Add mapper**
3. Set **Mapper type** to **Username Transform Mapper**
4. Set **Username template** to the desired rule, e.g. `${username}-foo`
5. **Save**

The mapper will apply to all users authenticating through that IdP from the next login onwards. Existing federated users will have their local username updated on their next login via `updateBrokeredUser`.

## SAML IdP considerations

### Principal attribute

The incoming username is sourced from the SAML assertion's principal. When the IdP uses transient NameIDs (as many test IdPs do), you must configure Keycloak to use a stable SAML attribute as the principal instead:

1. Open the IdP → **Settings** → scroll to **Principal type** → set to **Attribute**
2. Set **Principal attribute** to the SAML attribute that carries the username (e.g. `cn`)

The `cn` attribute typically contains the login name (`user1`, `user2`). Avoid `uid` if it is a numeric identifier.

### Profile attributes

To avoid Keycloak prompting users to complete their profile on first login, the SAML IdP should assert `givenName`, `sn`, and `mail` attributes, and the IdP must have corresponding **Attribute mappers** in addition to the Username Transform Mapper:

| Mapper type | SAML attribute | Keycloak user attribute |
|-------------|----------------|-------------------------|
| Attribute Importer | `givenName` | `firstName` |
| Attribute Importer | `sn` | `lastName` |
| Attribute Importer | `mail` | `email` |

Without these, Keycloak's user profile validation will trigger a **Verify Profile** or **Update Account Information** screen after the first federation login. You should also disable the **VERIFY_PROFILE** required action in the realm (**Authentication** → **Required actions**) if you do not want users prompted to fill in missing fields.

## Building

```sh
mvn package -DskipTests
# output: target/keycloak-custom-idp-mapper.jar
```

Copy the JAR to `/opt/keycloak/providers/` and restart Keycloak.
