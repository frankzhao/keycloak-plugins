package net.frankzhao.keycloak;

import org.keycloak.Config;
import org.keycloak.authentication.Authenticator;
import org.keycloak.authentication.AuthenticatorFactory;
import org.keycloak.models.AuthenticationExecutionModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.KeycloakSessionFactory;
import org.keycloak.provider.ProviderConfigProperty;

import java.util.Collections;
import java.util.List;

public class JustificationAuthenticatorFactory implements AuthenticatorFactory {

    public static final String PROVIDER_ID = "justification-authenticator";

    private static final JustificationAuthenticator SINGLETON = new JustificationAuthenticator();

    private static final AuthenticationExecutionModel.Requirement[] REQUIREMENT_CHOICES = {
            AuthenticationExecutionModel.Requirement.REQUIRED,
            AuthenticationExecutionModel.Requirement.ALTERNATIVE,
            AuthenticationExecutionModel.Requirement.DISABLED
    };

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public String getDisplayType() {
        return "Login Justification Form";
    }

    @Override
    public String getHelpText() {
        return "Displays a justification form after login and persists the user's justification, " +
               "reason, username, timestamp, and redirect URL to the database.";
    }

    @Override
    public String getReferenceCategory() {
        return "justification";
    }

    @Override
    public boolean isConfigurable() {
        return false;
    }

    @Override
    public AuthenticationExecutionModel.Requirement[] getRequirementChoices() {
        return REQUIREMENT_CHOICES;
    }

    @Override
    public boolean isUserSetupAllowed() {
        return false;
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return Collections.emptyList();
    }

    @Override
    public Authenticator create(KeycloakSession session) {
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
