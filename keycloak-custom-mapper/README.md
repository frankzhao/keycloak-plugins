# keycloak-custom-mapper

A Keycloak Protocol Mapper SPI that appends a configurable suffix to the login username and writes the result into a token claim.

The stored username in Keycloak is never modified — the transformation is applied at token issuance time only.

## How it works

At token issuance, the mapper reads the user's username, appends the configured suffix, and writes it to the configured claim name via `otherClaims`. Because `otherClaims` is serialised after the standard IDToken fields, it takes precedence over the built-in `preferred_username` mapper without needing to disable it.

## Provider

| SPI | ID | Class |
|-----|----|-------|
| ProtocolMapper | `username-suffix-mapper` | `UsernameSuffixMapper` |

Applies to: access token, ID token, userinfo endpoint.

## Configuration

The mapper is configured per client scope in the Keycloak Admin Console:

| Field | Default | Description |
|-------|---------|-------------|
| **Username suffix** | _(empty)_ | String appended to the username, e.g. `@example.com` |
| **Claim name** | `preferred_username` | Token claim that receives the transformed value |
| **Add to ID token** | — | Include in ID token |
| **Add to access token** | — | Include in access token |
| **Add to userinfo** | — | Include in userinfo endpoint response |

All three token inclusion checkboxes must be enabled for the mapper to apply.

## Wiring up the mapper

1. **Clients** → select your client → **Client scopes** tab
2. Click the `<client>-dedicated` scope
3. **Mappers** tab → **Add mapper** → **By configuration**
4. Select **Username Suffix Mapper**
5. Set **Username suffix** and **Claim name**, enable the token inclusion checkboxes
6. **Save**

## Building

```sh
mvn package -DskipTests
# output: target/keycloak-custom-mapper.jar
```

Copy the JAR to `/opt/keycloak/providers/` and restart Keycloak.
