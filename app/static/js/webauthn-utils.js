// WebAuthn utility functions
export function base64urlToBuffer(input) {
    if (!input) {
        console.error('base64urlToBuffer received undefined/null input');
        throw new Error('Cannot convert undefined/null to ArrayBuffer');
    }
    console.debug('Converting base64url to buffer:', input);
    const base64 = input.replace(/-/g, '+').replace(/_/g, '/');
    const padding = '='.repeat((4 - base64.length % 4) % 4);
    const binary = window.atob(base64 + padding);
    const buffer = new ArrayBuffer(binary.length);
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
    }
    return buffer;
}

export function bufferToBase64url(buffer) {
    if (!buffer) {
        console.error('bufferToBase64url received undefined/null buffer');
        throw new Error('Cannot convert undefined/null buffer to base64url');
    }
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    const base64 = window.btoa(binary);
    return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

// Check if browser supports WebAuthn
export function isWebAuthnSupported() {
    return window.PublicKeyCredential !== undefined &&
           typeof window.PublicKeyCredential === 'function';
}

// Convert public key credential options for WebAuthn registration
export function prepareRegistrationCredentialOptions(options) {
    console.debug('Preparing registration options:', JSON.stringify(options, null, 2));
    
    if (!options) {
        console.error('prepareRegistrationCredentialOptions received undefined/null options');
        throw new Error('Cannot prepare undefined/null credential options');
    }

    // If options is a string, try to parse it
    if (typeof options === 'string') {
        try {
            options = JSON.parse(options);
        } catch (error) {
            console.error('Failed to parse options string:', error);
            throw new Error('Invalid options format: must be an object or valid JSON string');
        }
    }

    // Validate required fields for registration
    const requiredFields = ['challenge', 'rp', 'user', 'pubKeyCredParams'];
    const missingFields = requiredFields.filter(field => !options[field]);
    
    if (missingFields.length > 0) {
        console.error('Missing required fields in options:', missingFields);
        console.error('Received options:', JSON.stringify(options, null, 2));
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }

    if (!options.user.id) {
        console.error('Missing user.id in options:', JSON.stringify(options.user, null, 2));
        throw new Error('User ID is required for credential options');
    }

    try {
        return {
            challenge: base64urlToBuffer(options.challenge),
            rp: options.rp,
            user: {
                ...options.user,
                id: base64urlToBuffer(options.user.id),
            },
            pubKeyCredParams: options.pubKeyCredParams,
            timeout: options.timeout || 30000,
            excludeCredentials: (options.excludeCredentials || []).map(credential => ({
                ...credential,
                id: credential.id ? base64urlToBuffer(credential.id) : undefined,
            })).filter(cred => cred.id !== undefined),
            authenticatorSelection: options.authenticatorSelection || {
                authenticatorAttachment: "platform",
                residentKey: "required",
                requireResidentKey: true,
                userVerification: "preferred"
            },
            attestation: options.attestation || "none",
        };
    } catch (error) {
        console.error('Error preparing registration options:', error);
        throw error;
    }
}

// Convert public key credential options for WebAuthn authentication
export function prepareAuthenticationCredentialOptions(options) {
    console.debug('Preparing authentication options:', JSON.stringify(options, null, 2));
    
    if (!options) {
        console.error('prepareAuthenticationCredentialOptions received undefined/null options');
        throw new Error('Cannot prepare undefined/null credential options');
    }

    // If options is a string, try to parse it
    if (typeof options === 'string') {
        try {
            options = JSON.parse(options);
        } catch (error) {
            console.error('Failed to parse options string:', error);
            throw new Error('Invalid options format: must be an object or valid JSON string');
        }
    }

    // Validate required fields for authentication
    const requiredFields = ['challenge', 'allowCredentials'];
    const missingFields = requiredFields.filter(field => !options[field]);
    
    if (missingFields.length > 0) {
        console.error('Missing required fields in options:', missingFields);
        console.error('Received options:', JSON.stringify(options, null, 2));
        throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
    }

    try {
        return {
            challenge: base64urlToBuffer(options.challenge),
            timeout: options.timeout || 30000,
            rpId: options.rpId,
            allowCredentials: options.allowCredentials.map(credential => ({
                type: credential.type,
                id: base64urlToBuffer(credential.id),
                transports: credential.transports
            })),
            userVerification: options.userVerification || "preferred"
        };
    } catch (error) {
        console.error('Error preparing authentication options:', error);
        throw error;
    }
}

// For backward compatibility
export const preparePublicKeyCredentialOptions = prepareRegistrationCredentialOptions;

// Prepare credential data for server verification
export function prepareCredentialDataForServer(credential) {
    if (!credential) {
        throw new Error('No credential provided');
    }

    console.debug('Preparing credential data:', {
        id: credential.id,
        type: credential.type,
        response: {
            authenticatorData: 'present',
            clientDataJSON: 'present',
            signature: 'present',
            userHandle: credential.response.userHandle ? 'present' : 'absent'
        }
    });

    // For AuthenticationCredential
    if (credential.response instanceof AuthenticatorAssertionResponse) {
        const response = credential.response;
        return {
            id: credential.id,
            type: credential.type,
            rawId: bufferToBase64url(credential.rawId),
            response: {
                authenticatorData: bufferToBase64url(response.authenticatorData),
                clientDataJSON: bufferToBase64url(response.clientDataJSON),
                signature: bufferToBase64url(response.signature),
                userHandle: response.userHandle ? bufferToBase64url(response.userHandle) : null
            }
        };
    }
    // For RegistrationCredential
    else if (credential.response instanceof AuthenticatorAttestationResponse) {
        const response = credential.response;
        return {
            id: credential.id,
            type: credential.type,
            rawId: bufferToBase64url(credential.rawId),
            response: {
                attestationObject: bufferToBase64url(response.attestationObject),
                clientDataJSON: bufferToBase64url(response.clientDataJSON),
            }
        };
    }
    else {
        throw new Error('Unknown credential type');
    }
}

// Helper function to validate required fields in credential response
function validateCredentialResponse(credential) {
    if (!credential) {
        throw new Error('No credential provided');
    }

    const response = credential.response;
    const requiredFields = ['authenticatorData', 'signature', 'clientDataJSON'];
    const missingFields = requiredFields.filter(field => !response[field]);

    if (missingFields.length > 0) {
        console.error('Missing required response fields:', {
            credential: {
                id: credential.id,
                type: credential.type,
                response: {
                    authenticatorData: response.authenticatorData ? 'present' : 'missing',
                    signature: response.signature ? 'present' : 'missing',
                    clientDataJSON: response.clientDataJSON ? 'present' : 'missing',
                    userHandle: response.userHandle ? 'present' : 'missing'
                }
            }
        });
        throw new Error('Credential response missing required fields');
    }
}
