# keycloak-custom-login

A Keycloak Authenticator SPI that intercepts the browser login flow and presents a justification form. The user's response — along with their username, timestamp, and redirect URL — is persisted to a PostgreSQL table.

## How it works

After the standard username/password step, Keycloak invokes this authenticator. It renders a custom FreeMarker form asking for:

- **Justification** — free-text description of why access is needed
- **Reason** — short reason/reference (e.g. ticket number)

On submission the authenticator writes a record to the database and calls `context.success()` to complete the flow.

## Providers

| SPI | ID | Class |
|-----|----|-------|
| Authenticator | `justification-authenticator` | `JustificationAuthenticator` |
| ThemeResourceProvider | `justification-theme-resources` | `JustificationThemeResourceProvider` |

The `ThemeResourceProvider` serves `justification-form.ftl` from inside the JAR so no separate theme deployment is needed.

## Configuration

All configuration is via environment variables on the Keycloak container:

| Variable | Default | Description |
|----------|---------|-------------|
| `KC_DB_URL` | `jdbc:postgresql://postgres:5432/keycloak` | JDBC URL for the database |
| `KC_DB_USERNAME` | `keycloak` | Database username |
| `KC_DB_PASSWORD` | `keycloak` | Database password |
| `JUSTIFICATION_TABLE` | `login_justifications` | Table name for justification records |

## Database schema

Created automatically on first use:

```sql
CREATE TABLE IF NOT EXISTS login_justifications (
  id            BIGSERIAL PRIMARY KEY,
  username      VARCHAR(255) NOT NULL,
  justification TEXT         NOT NULL,
  reason        TEXT         NOT NULL,
  redirect_url  TEXT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

## Wiring up the authenticator

1. **Authentication** → **Flows** → duplicate the **browser** flow
2. In the new flow, click **Add step** → search **Login Justification Form** → **Add**
3. Drag it to the end of the flow and set requirement to **Required**
4. **Authentication** → **Bindings** → set **Browser flow** to the new flow

## Building

```sh
mvn package -DskipTests
# output: target/keycloak-custom-login.jar
```

Copy the JAR to `/opt/keycloak/providers/` and restart Keycloak.
