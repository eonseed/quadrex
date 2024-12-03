document.addEventListener('DOMContentLoaded', function() {
    const removePasskeyButton = document.getElementById('remove-passkey-btn');

    if (removePasskeyButton) {
        removePasskeyButton.addEventListener('click', async function() {
            try {
                const response = await fetch('/auth/passkey/remove', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Failed to remove passkey');
                }

                const result = await response.json();
                console.log('Passkey removed successfully:', result);

                // Update the UI to reflect the removal
                document.getElementById('passkey-success').classList.add('hidden');
                document.getElementById('passkey-error').classList.add('hidden');
                document.getElementById('register-passkey-btn').classList.remove('hidden');
                removePasskeyButton.classList.add('hidden');

                // Optionally, you can show a success message
                const successMessage = document.getElementById('passkey-success-message');
                if (successMessage) {
                    successMessage.textContent = 'Passkey removed successfully.';
                    document.getElementById('passkey-success').classList.remove('hidden');
                }

            } catch (error) {
                console.error('Error removing passkey:', error);
                const errorMessage = document.getElementById('passkey-error-message');
                if (errorMessage) {
                    errorMessage.textContent = error.message || 'Failed to remove passkey. Please try again.';
                    document.getElementById('passkey-error').classList.remove('hidden');
                }
            }
        });
    }
});
