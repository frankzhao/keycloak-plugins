package net.frankzhao.keycloak;

import org.jboss.logging.Logger;

import java.sql.*;
import java.time.Instant;

/**
 * Handles all database operations for login justifications.
 * Uses the same PostgreSQL instance as Keycloak, reading connection
 * details from standard Keycloak environment variables.
 */
public class JustificationDatabase {

    private static final Logger log = Logger.getLogger(JustificationDatabase.class);

    private static final String JDBC_URL = System.getenv().getOrDefault(
            "KC_DB_URL", "jdbc:postgresql://postgres:5432/keycloak");
    private static final String DB_USER = System.getenv().getOrDefault(
            "KC_DB_USERNAME", "keycloak");
    private static final String DB_PASSWORD = System.getenv().getOrDefault(
            "KC_DB_PASSWORD", "keycloak");
    private static final String TABLE_NAME = System.getenv().getOrDefault(
            "JUSTIFICATION_TABLE", "login_justifications");

    private static final String CREATE_TABLE_SQL =
            "CREATE TABLE IF NOT EXISTS " + TABLE_NAME + " (" +
            "  id          BIGSERIAL PRIMARY KEY," +
            "  username    VARCHAR(255) NOT NULL," +
            "  justification TEXT NOT NULL," +
            "  reason      TEXT NOT NULL," +
            "  redirect_url TEXT," +
            "  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()" +
            ")";

    private static final String INSERT_SQL =
            "INSERT INTO " + TABLE_NAME + " (username, justification, reason, redirect_url, created_at) " +
            "VALUES (?, ?, ?, ?, ?)";

    private static volatile boolean tableEnsured = false;

    private static Connection getConnection() throws SQLException {
        return DriverManager.getConnection(JDBC_URL, DB_USER, DB_PASSWORD);
    }

    private static void ensureTable(Connection conn) throws SQLException {
        if (tableEnsured) return;
        try (Statement st = conn.createStatement()) {
            st.execute(CREATE_TABLE_SQL);
            conn.commit();
        } catch (SQLException e) {
            // Table may already exist or auto-commit is on — either is fine
            log.debugf("ensureTable: %s", e.getMessage());
        }
        tableEnsured = true;
    }

    /**
     * Persists a login justification record.
     *
     * @param username      Keycloak username
     * @param justification Free-text justification entered by the user
     * @param reason        Selected/entered reason
     * @param redirectUrl   The redirect_uri of the client the user is logging into
     */
    public static void save(String username, String justification, String reason, String redirectUrl) {
        try (Connection conn = getConnection()) {
            ensureTable(conn);
            try (PreparedStatement ps = conn.prepareStatement(INSERT_SQL)) {
                ps.setString(1, username);
                ps.setString(2, justification);
                ps.setString(3, reason);
                ps.setString(4, redirectUrl);
                ps.setTimestamp(5, Timestamp.from(Instant.now()));
                ps.executeUpdate();
            }
            log.infof("Justification saved for user '%s' (url=%s)", username, redirectUrl);
        } catch (SQLException e) {
            // Log but do not block login — DB failures should not lock users out
            log.errorf(e, "Failed to save justification for user '%s'", username);
        }
    }
}
