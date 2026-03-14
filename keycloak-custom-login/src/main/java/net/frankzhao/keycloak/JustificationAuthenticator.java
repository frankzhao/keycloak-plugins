package net.frankzhao.keycloak;

import org.jboss.logging.Logger;
import org.keycloak.authentication.AuthenticationFlowContext;
import org.keycloak.authentication.AuthenticationFlowError;
import org.keycloak.authentication.Authenticator;
import org.keycloak.models.KeycloakSession;
import org.keycloak.models.RealmModel;
import org.keycloak.models.UserModel;

import jakarta.ws.rs.core.MultivaluedMap;
import jakarta.ws.rs.core.Response;

public class JustificationAuthenticator implements Authenticator {

    private static final Logger log = Logger.getLogger(JustificationAuthenticator.class);

    static final String FORM_TEMPLATE = "justification-form.ftl";
    static final String FIELD_JUSTIFICATION = "justification";
    static final String FIELD_REASON = "reason";

    @Override
    public void authenticate(AuthenticationFlowContext context) {
        Response response = context.form()
                .createForm(FORM_TEMPLATE);
        context.challenge(response);
    }

    @Override
    public void action(AuthenticationFlowContext context) {
        MultivaluedMap<String, String> formData = context.getHttpRequest()
                .getDecodedFormParameters();

        String justification = formData.getFirst(FIELD_JUSTIFICATION);
        String reason = formData.getFirst(FIELD_REASON);

        if (isBlank(justification) || isBlank(reason)) {
            Response response = context.form()
                    .setError("justificationRequired")
                    .createForm(FORM_TEMPLATE);
            context.failureChallenge(AuthenticationFlowError.INVALID_CREDENTIALS, response);
            return;
        }

        String username = context.getUser() != null
                ? context.getUser().getUsername()
                : "unknown";

        String redirectUrl = context.getAuthenticationSession().getRedirectUri();

        JustificationDatabase.save(username, justification, reason, redirectUrl);

        context.success();
    }

    @Override
    public boolean requiresUser() {
        // Must run after the user has been identified
        return true;
    }

    @Override
    public boolean configuredFor(KeycloakSession session, RealmModel realm, UserModel user) {
        return true;
    }

    @Override
    public void setRequiredActions(KeycloakSession session, RealmModel realm, UserModel user) {
        // No required actions needed
    }

    @Override
    public void close() {
        // Nothing to close
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }
}
