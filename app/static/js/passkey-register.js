import { isWebAuthnSupported, preparePublicKeyCredentialOptions, prepareCredentialDataForServer } from '/js/webauthn-utils.js';

class PasskeyManager {
    constructor() {
        // Initialize DOM elements
        this.registerButton = document.getElementById('register-passkey-btn');
        this.errorContainer = document.getElementById('passkey-error');
        this.errorMessage = document.getElementById('passkey-error-message');
        this.successContainer = document.getElementById('passkey-success');
        this.successMessage = document.getElementById('passkey-success-message');
        this.loadingContainer = document.getElementById('passkey-loading');

        // Initialize if button exists
        if (this.registerButton) {
            this.init();
        }
    }

    showError(message) {
        if (this.errorContainer && this.errorMessage) {
            this.errorMessage.textContent = message;
            this.errorContainer.classList.remove('hidden');
            this.successContainer?.classList.add('hidden');
            setTimeout(() => this.errorContainer.classList.add('hidden'), 5000);
        }
        console.error('Passkey error:', message);
    }

    showSuccess(message) {
        if (this.successContainer && this.successMessage) {
            this.successMessage.textContent = message;
            this.successContainer.classList.remove('hidden');
            this.errorContainer?.classList.add('hidden');
            setTimeout(() => this.successContainer.classList.add('hidden'), 5000);
        }
        console.log('Passkey success:', message);
    }

    setLoading(loading) {
        if (!this.registerButton || !this.loadingContainer) return;

        if (loading) {
            this.loadingContainer.classList.remove('hidden');
            this.registerButton.disabled = true;
            this.registerButton.classList.add('btn-disabled');
        } else {
            this.loadingContainer.classList.add('hidden');
            this.registerButton.disabled = false;
            this.registerButton.classList.remove('btn-disabled');
        }
    }

    async registerPasskey() {
        try {
            console.log('Starting passkey registration...');
            this.setLoading(true);

            // Check if browser supports WebAuthn
            if (!isWebAuthnSupported()) {
                throw new Error('Your browser does not support passkeys. Please use a modern browser.');
            }

            // Get registration options from server
            const optionsRes = await fetch('/auth/passkey/register/options', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });

            if (!optionsRes.ok) {
                const error = await optionsRes.json();
                throw new Error(error.error || 'Failed to start registration');
            }

            const optionsText = await optionsRes.text();
            console.debug('Raw server response:', optionsText);
            
            let options;
            try {
                options = JSON.parse(optionsText);
            } catch (error) {
                console.error('Failed to parse server response:', error);
                throw new Error('Invalid server response format');
            }
            
            console.debug('Parsed registration options:', JSON.stringify(options, null, 2));

            // Prepare the options for WebAuthn API
            console.debug('Calling preparePublicKeyCredentialOptions with:', JSON.stringify(options, null, 2));
            const publicKeyCredentialOptions = preparePublicKeyCredentialOptions(options);
            console.debug('Prepared credential options:', JSON.stringify(publicKeyCredentialOptions, null, 2));

            // Create credentials
            console.log('Creating credentials...');
            const credential = await navigator.credentials.create({
                publicKey: publicKeyCredentialOptions
            });

            if (!credential) {
                throw new Error('Failed to create passkey. Please try again.');
            }

            console.log('Credentials created:', {
                id: credential.id,
                type: credential.type,
                response: {
                    attestationObject: 'present',
                    clientDataJSON: 'present',
                    getTransports: typeof credential.response.getTransports === 'function'
                }
            });

            // Prepare credential data for server
            console.log('Preparing registration data for server verification...');
            const registrationData = prepareCredentialDataForServer(credential);

            // Send credential to server for verification
            console.log('Sending registration data to server...');
            let verifyRes;
            try {
                verifyRes = await fetch('/auth/passkey/register/verify', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(registrationData)
                });

                const responseText = await verifyRes.text();
                console.log('Server response:', responseText);

                let responseData;
                try {
                    responseData = JSON.parse(responseText);
                } catch (e) {
                    console.error('Failed to parse server response:', e);
                    throw new Error('Invalid server response format');
                }

                if (!verifyRes.ok) {
                    console.error('Server verification failed:', responseData);
                    throw new Error(responseData.error || 'Failed to verify registration');
                }

                console.log('Server verification successful:', responseData);
                this.showSuccess('Passkey registered successfully! You can now use it to sign in.');
                
                // Delay reload to show success message
                await new Promise(resolve => setTimeout(resolve, 2000));
                window.location.reload();

            } catch (error) {
                console.error('Verification request failed:', error);
                throw new Error(`Registration verification failed: ${error.message}`);
            }

        } catch (error) {
            console.error('Registration error:', error);
            this.showError(error.message || 'Failed to register passkey. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    init() {
        // Check WebAuthn support
        if (!isWebAuthnSupported()) {
            this.showError('Your browser does not support passkeys. Please use a modern browser.');
            this.registerButton.disabled = true;
            this.registerButton.classList.add('btn-disabled');
            return;
        }

        // Add click event listener
        this.registerButton.addEventListener('click', () => {
            console.log('Register button clicked');
            this.registerPasskey();
        });
        console.log('Passkey registration initialized');
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing PasskeyManager');
    new PasskeyManager();
});
