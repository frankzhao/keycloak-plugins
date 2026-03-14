<#import "template.ftl" as layout>

<@layout.registrationLayout displayMessage=!messagesPerField.existsError('justification', 'reason'); section>

    <#if section = "header">
        Access Justification

    <#elseif section = "form">
        <p class="pf-v5-u-mb-md" style="color: var(--pf-v5-global--Color--200);">
            Please provide a justification for accessing this resource. Your response will be logged.
        </p>

        <form id="kc-justification-form"
              class="${properties.kcFormClass!}"
              action="${url.loginAction}"
              method="post">

            <#-- Justification field -->
            <div class="${properties.kcFormGroupClass!}">
                <label for="justification" class="${properties.kcLabelClass!}">
                    Justification <span style="color:red">*</span>
                </label>
                <textarea id="justification"
                          name="justification"
                          class="${properties.kcInputClass!}"
                          rows="4"
                          placeholder="Describe why you need access to this resource..."
                          autofocus
                          required>${(justification)!''}</textarea>
                <#if messagesPerField.existsError('justification')>
                    <span class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('justification'))?no_esc}
                    </span>
                </#if>
            </div>

            <#-- Reason field -->
            <div class="${properties.kcFormGroupClass!}">
                <label for="reason" class="${properties.kcLabelClass!}">
                    Reason <span style="color:red">*</span>
                </label>
                <input type="text"
                       id="reason"
                       name="reason"
                       class="${properties.kcInputClass!}"
                       placeholder="e.g. Support ticket #1234, Scheduled maintenance, etc."
                       value="${(reason)!''}"
                       required />
                <#if messagesPerField.existsError('reason')>
                    <span class="${properties.kcInputErrorMessageClass!}" aria-live="polite">
                        ${kcSanitize(messagesPerField.get('reason'))?no_esc}
                    </span>
                </#if>
            </div>

            <#-- Submit -->
            <div class="${properties.kcFormGroupClass!}">
                <div id="kc-form-buttons" class="${properties.kcFormButtonsClass!}">
                    <input class="${properties.kcButtonClass!} ${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} ${properties.kcButtonLargeClass!}"
                           type="submit"
                           value="Continue" />
                </div>
            </div>

        </form>
    </#if>

</@layout.registrationLayout>
