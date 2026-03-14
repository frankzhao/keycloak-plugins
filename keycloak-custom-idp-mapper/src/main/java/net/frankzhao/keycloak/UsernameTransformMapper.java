package net.frankzhao.keycloak;

import org.jboss.logging.Logger;
import org.keycloak.broker.provider.AbstractIdentityProviderMapper;
import org.keycloak.broker.provider.BrokeredIdentityContext;
import org.keycloak.models.IdentityProviderMapperModel;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;
import org.keycloak.provider.ProviderConfigProperty;

import java.util.ArrayList;
import java.util.List;

/**
 * Identity Provider Mapper that applies a configurable transformation rule to
 * the incoming username before Keycloak looks up or creates the local user.
 *
 * The rule uses a template where ${username} is replaced with the incoming
 * username. For example, the template "${username}-foo" maps "alice" → "alice-foo".
 *
 * Compatible with any Identity Provider (SAML, OIDC, social, etc.).
 */
public class UsernameTransformMapper extends AbstractIdentityProviderMapper {

    private static final Logger log = Logger.getLogger(UsernameTransformMapper.class);

    public static final String PROVIDER_ID = "username-transform-mapper";

    static final String PROP_TEMPLATE = "username.template";

    private static final List<ProviderConfigProperty> CONFIG_PROPERTIES = new ArrayList<>();

    static {
        ProviderConfigProperty template = new ProviderConfigProperty();
        template.setName(PROP_TEMPLATE);
        template.setLabel("Username template");
        template.setType(ProviderConfigProperty.STRING_TYPE);
        template.setHelpText(
                "Transformation template applied to the incoming username. " +
                "Use ${username} as a placeholder for the original value. " +
                "Example: \"${username}-foo\" maps \"alice\" to \"alice-foo\".");
        template.setDefaultValue("${username}");
        CONFIG_PROPERTIES.add(template);
    }

    // Applies to every identity provider
    private static final String[] COMPATIBLE_PROVIDERS = {ANY_PROVIDER};

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public String getDisplayType() {
        return "Username Transform Mapper";
    }

    @Override
    public String getDisplayCategory() {
        return "Username Mapper";
    }

    @Override
    public String getHelpText() {
        return "Transforms the incoming username using a configurable template before " +
               "it is matched against a local Keycloak user.";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return CONFIG_PROPERTIES;
    }

    @Override
    public String[] getCompatibleProviders() {
        return COMPATIBLE_PROVIDERS;
    }

    /**
     * Called before the federated identity is looked up or created.
     * This is the right place to rewrite the username used for local user matching.
     */
    @Override
    public void preprocessFederatedIdentity(KeycloakSession session,
                                            RealmModel realm,
                                            IdentityProviderMapperModel mapperModel,
                                            BrokeredIdentityContext context) {
        String incoming    = context.getUsername();
        String transformed = apply(mapperModel, incoming);
        log.debugf("UsernameTransformMapper: '%s' -> '%s'", incoming, transformed);
        context.setModelUsername(transformed);
    }

    /**
     * Called when an existing federated user logs in again.
     * Keeps the local username in sync with the transformation rule.
     */
    @Override
    public void updateBrokeredUser(KeycloakSession session,
                                   RealmModel realm,
                                   UserModel user,
                                   IdentityProviderMapperModel mapperModel,
                                   BrokeredIdentityContext context) {
        String incoming    = context.getUsername();
        String transformed = apply(mapperModel, incoming);
        if (!transformed.equals(user.getUsername())) {
            log.debugf("UsernameTransformMapper: updating username '%s' -> '%s'",
                    user.getUsername(), transformed);
            user.setUsername(transformed);
        }
    }

    private static String apply(IdentityProviderMapperModel mapperModel, String username) {
        String template = mapperModel.getConfig()
                .getOrDefault(PROP_TEMPLATE, "${username}");
        return template.replace("${username}", username);
    }
}
