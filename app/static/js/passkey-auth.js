import { isWebAuthnSupported, prepareAuthenticationCredentialOptions, prepareCredentialDataForServer } from './webauthn-utils.js';

class PasskeyAuth {
    constructor() {
        this.form = document.getElementById('passkey-auth-form');
        this.emailInput = document.getElementById('email');
        this.submitButton = document.getElementById('submit-button');
        this.errorDisplay = document.getElementById('error-message');
        this.loadingIndicator = document.getElementById('loading-indicator');
        
        this.init();
    }

    showError(message) {
        if (this.errorDisplay) {
            this.errorDisplay.textContent = message;
            this.errorDisplay.style.display = 'block';
        }
    }

    hideError() {
        if (this.errorDisplay) {
            this.errorDisplay.style.display = 'none';
        }
    }

    setLoading(isLoading) {
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = isLoading ? 'block' : 'none';
        }
        if (this.submitButton) {
            this.submitButton.disabled = isLoading;
        }
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        try {
            this.hideError();
            this.setLoading(true);

            // Get email if provided
            const email = this.emailInput ? this.emailInput.value.trim() : null;
            
            // Check if WebAuthn is supported
            if (!isWebAuthnSupported()) {
                throw new Error('WebAuthn is not supported in this browser');
            }

            // Get authentication options from server
            const response = await fetch('/auth/passkey/authenticate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to get authentication options');
            }

            const options = await response.json();
            console.log('Received options:', JSON.stringify(options, null, 2));

            // Convert options for WebAuthn
            const publicKeyCredentialRequestOptions = prepareAuthenticationCredentialOptions(options);
            console.log('Prepared options:', publicKeyCredentialRequestOptions);

            // Get credentials
            const credential = await navigator.credentials.get({
                publicKey: publicKeyCredentialRequestOptions
            });

            if (!credential) {
                throw new Error('No credentials received from authenticator');
            }

            // Prepare credential data for server
            const credentialData = prepareCredentialDataForServer(credential);
            console.log('Prepared credential data:', credentialData);

            // Send credential to server for verification
            const verifyResponse = await fetch('/auth/passkey/authenticate/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(credentialData),
            });

            if (!verifyResponse.ok) {
                const error = await verifyResponse.json();
                throw new Error(error.error || 'Failed to verify authentication');
            }

            const result = await verifyResponse.json();
            console.log('Authentication successful:', result);

            // Redirect to success page
            window.location.href = '/';

        } catch (error) {
            console.error('Authentication error:', error);
            this.showError(error.message || 'Authentication failed');
        } finally {
            this.setLoading(false);
        }
    }

    init() {
        if (this.form) {
            this.form.addEventListener('submit', this.handleSubmit.bind(this));
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PasskeyAuth();
});

export default PasskeyAuth;
