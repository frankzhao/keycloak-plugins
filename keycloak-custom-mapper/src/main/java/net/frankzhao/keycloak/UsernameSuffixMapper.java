package net.frankzhao.keycloak;

import org.jboss.logging.Logger;
import org.keycloak.models.ClientSessionContext;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.ProtocolMapperModel;
import org.keycloak.models.UserSessionModel;
import org.keycloak.protocol.oidc.mappers.AbstractOIDCProtocolMapper;
import org.keycloak.protocol.oidc.mappers.OIDCAccessTokenMapper;
import org.keycloak.protocol.oidc.mappers.OIDCAttributeMapperHelper;
import org.keycloak.protocol.oidc.mappers.OIDCIDTokenMapper;
import org.keycloak.protocol.oidc.mappers.UserInfoTokenMapper;
import org.keycloak.provider.ProviderConfigProperty;
import org.keycloak.representations.IDToken;

import java.util.ArrayList;
import java.util.List;

/**
 * OIDC Protocol Mapper that appends a configurable suffix to the username
 * and writes the result into a configurable token claim.
 *
 * Applies to: access token, ID token, and userinfo endpoint.
 */
public class UsernameSuffixMapper extends AbstractOIDCProtocolMapper
        implements OIDCAccessTokenMapper, OIDCIDTokenMapper, UserInfoTokenMapper {

    private static final Logger log = Logger.getLogger(UsernameSuffixMapper.class);

    public static final String PROVIDER_ID = "username-suffix-mapper";

    static final String PROP_SUFFIX = "username.suffix";
    static final String PROP_CLAIM  = "claim.name";

    private static final List<ProviderConfigProperty> CONFIG_PROPERTIES = new ArrayList<>();

    static {
        ProviderConfigProperty suffix = new ProviderConfigProperty();
        suffix.setName(PROP_SUFFIX);
        suffix.setLabel("Username suffix");
        suffix.setType(ProviderConfigProperty.STRING_TYPE);
        suffix.setHelpText("String appended to the username, e.g. \"@example.com\".");
        suffix.setDefaultValue("");
        CONFIG_PROPERTIES.add(suffix);

        ProviderConfigProperty claimName = new ProviderConfigProperty();
        claimName.setName(PROP_CLAIM);
        claimName.setLabel("Claim name");
        claimName.setType(ProviderConfigProperty.STRING_TYPE);
        claimName.setHelpText(
                "Token claim that will receive the transformed username. " +
                "Use \"preferred_username\" to override the standard claim.");
        claimName.setDefaultValue("preferred_username");
        CONFIG_PROPERTIES.add(claimName);

        // Adds "Add to ID token", "Add to access token", "Add to userinfo" checkboxes.
        // AbstractOIDCProtocolMapper gates setClaim() on these — without them the mapper
        // silently skips every token.
        OIDCAttributeMapperHelper.addIncludeInTokensConfig(CONFIG_PROPERTIES, UsernameSuffixMapper.class);
    }

    @Override
    public String getId() {
        return PROVIDER_ID;
    }

    @Override
    public String getDisplayType() {
        return "Username Suffix Mapper";
    }

    @Override
    public String getDisplayCategory() {
        return TOKEN_MAPPER_CATEGORY;
    }

    @Override
    public String getHelpText() {
        return "Appends a configurable suffix to the login username and sets it in a token claim.";
    }

    @Override
    public List<ProviderConfigProperty> getConfigProperties() {
        return CONFIG_PROPERTIES;
    }

    @Override
    protected void setClaim(IDToken token,
                            ProtocolMapperModel mappingModel,
                            UserSessionModel userSession,
                            KeycloakSession keycloakSession,
                            ClientSessionContext clientSessionCtx) {

        String suffix    = mappingModel.getConfig().getOrDefault(PROP_SUFFIX, "");
        String claimName = mappingModel.getConfig().getOrDefault(PROP_CLAIM, "preferred_username");
        String username  = userSession.getUser().getUsername();
        String transformed = username + suffix;

        log.debugf("UsernameSuffixMapper: '%s' -> '%s' (claim=%s)", username, transformed, claimName);

        // Always write via otherClaims. Keycloak serialises annotated IDToken fields first,
        // then @JsonAnyGetter (otherClaims), so our entry appears last in the JSON and
        // overrides any earlier value set by the built-in preferred_username mapper.
        token.getOtherClaims().put(claimName, transformed);
    }
}
