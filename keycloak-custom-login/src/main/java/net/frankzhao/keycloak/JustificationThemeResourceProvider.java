package net.frankzhao.keycloak;

import org.keycloak.theme.ThemeResourceProvider;

import java.io.IOException;
import java.io.InputStream;
import java.net.URL;

/**
 * Serves the justification FTL template and any static assets from the JAR,
 * making them available to Keycloak's theme engine without requiring a separate
 * theme deployment.
 */
public class JustificationThemeResourceProvider implements ThemeResourceProvider {

    @Override
    public URL getTemplate(String name) throws IOException {
        return getClass().getResource("/theme-resources/templates/" + name);
    }

    @Override
    public InputStream getResourceAsStream(String path) throws IOException {
        return getClass().getResourceAsStream("/theme-resources/" + path);
    }

    @Override
    public void close() {
        // Nothing to close
    }
}
