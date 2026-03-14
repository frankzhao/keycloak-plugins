package net.frankzhao.keycloak;

import org.keycloak.Config;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.theme.ThemeResourceProvider;
import org.keycloak.theme.ThemeResourceProviderFactory;

public class JustificationThemeResourceProviderFactory implements ThemeResourceProviderFactory {

    public static final String PROVIDER_ID = "justification-theme-resources";

    private static final JustificationThemeResourceProvider SINGLETON =
            new JustificationThemeResourceProvider();

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public ThemeResourceProvider create(KeycloakSession session) {
        return SINGLETON;
    }

    @Override
    public void init(Config.Scope config) {
        // Nothing to initialise
    }

    @Override
    public void postInit(KeycloakSessionFactory factory) {
        // Nothing to post-initialise
    }

    @Override
    public void close() {
        // Nothing to close
    }
}
