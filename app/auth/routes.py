from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db, csrf
from app.auth import bp
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers import (
    base64url_to_bytes,
    parse_registration_credential_json,
    parse_authentication_credential_json
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    AuthenticatorAttachment,
    AttestationConveyancePreference,
    RegistrationCredential,
    AuthenticationCredential,
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport
)
import base64
import json
from datetime import datetime
import os

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # Create default categories for the new user
        user.create_default_categories()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.change_password(form.current_password.data, form.new_password.data):
            db.session.commit()
            flash('Your password has been changed successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid current password.', 'error')
    return render_template('auth/change_password.html', title='Change Password', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/passkey/register/options', methods=['POST'])
@login_required
@csrf.exempt
def register_passkey():
    """Generate passkey registration options."""
    try:
        user = current_user
        
        # Check if user already has a passkey
        if user.has_passkey():
            return jsonify({
                'error': 'You already have a passkey registered. Please remove the existing one first.'
            }), 400
            
        display_name = user.username or user.email.split('@')[0]
        
        # Convert user ID to bytes
        user_id = str(user.id).encode('utf-8')
        
        try:
            # Create authenticator selection criteria
            authenticator_selection = AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                resident_key=ResidentKeyRequirement.REQUIRED,  
                user_verification=UserVerificationRequirement.PREFERRED  
            )
            
            # Generate registration options
            options = generate_registration_options(
                rp_id="localhost",  
                rp_name="Quadrex",
                user_id=user_id,
                user_name=user.email,
                user_display_name=display_name,
                authenticator_selection=authenticator_selection,
                timeout=30000,
                attestation=AttestationConveyancePreference.NONE
            )
            
            # Convert options to JSON-compatible format
            options_json = options_to_json(options)
            
            # Store challenge in session with timeout
            session['register_challenge'] = base64.b64encode(options.challenge).decode()
            session['register_timeout'] = datetime.utcnow().timestamp() + 30
            
            return jsonify(options_json)
            
        except Exception as e:
            print(f"Error generating registration options: {str(e)}")
            return jsonify({
                'error': f'Failed to generate registration options: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Error in register_passkey: {str(e)}")
        return jsonify({
            'error': f'Registration failed: {str(e)}'
        }), 500

@bp.route('/passkey/register/verify', methods=['POST'])
@login_required
@csrf.exempt
def verify_passkey_registration():
    """Verify and store the newly created passkey."""
    try:
        # Check timeout
        timeout = session.get('register_timeout')
        if not timeout or datetime.utcnow().timestamp() > timeout:
            return jsonify({
                'error': 'Registration timeout. Please try again.'
            }), 400

        # Get challenge from session
        challenge = session.get('register_challenge')
        if not challenge:
            return jsonify({
                'error': 'Invalid session state. Please try again.'
            }), 400

        try:
            # Parse the registration response
            data = request.get_json()
            print(f"Received registration data: {json.dumps(data, indent=2)}")
            
            # Parse the credential using webauthn helper
            credential = parse_registration_credential_json(json.dumps(data))
            print(f"Parsed credential object successfully")
            
        except Exception as e:
            print(f"Error parsing registration data: {str(e)}")
            print(f"Raw data: {request.get_data(as_text=True)}")
            return jsonify({
                'error': f'Invalid registration data: {str(e)}'
            }), 400

        try:
            # Get challenge from session for logging
            print(f"Session challenge: {challenge}")
            print(f"Expected origin: {request.url_root.rstrip('/')}")
            
            # Verify the registration response
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=base64.b64decode(challenge),
                expected_rp_id="localhost",
                expected_origin=request.url_root.rstrip('/'),
                require_user_verification=True
            )
            print(f"Verification successful: {verification}")
        except Exception as e:
            print(f"Registration verification error: {str(e)}")
            return jsonify({
                'error': f'Registration verification failed: {str(e)}'
            }), 400

        try:
            # Store the verified credential
            current_user.set_passkey(
                credential_id=base64.b64encode(credential.raw_id).decode(),
                public_key=base64.b64encode(verification.credential_public_key).decode()
            )
            db.session.commit()
            
            flash('Passkey registered successfully!', 'success')
            return jsonify({'status': 'success'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to save passkey. Please try again.'
            }), 500
            
    except Exception as e:
        print(f"Registration verification error: {str(e)}")
        return jsonify({
            'error': 'Registration failed. Please try again.'
        }), 400

@bp.route('/passkey/authenticate', methods=['POST'])
@csrf.exempt
def passkey_authenticate():
    """Generate options for passkey authentication."""
    try:
        data = request.get_json() or {}
        email = data.get('email')
        
        print(f"Authentication request data: {json.dumps(data, indent=2)}")
        
        # Initialize allow_credentials list
        allow_credentials = []
        
        if email:
            # If email provided, only allow that user's passkey
            user = User.query.filter_by(email=email).first()
            if not user or not user.has_passkey():
                return jsonify({
                    'error': 'No passkey found for this email address. Please register a passkey first.'
                }), 400
                
            try:
                credential_id = base64url_to_bytes(user.passkey_credential_id)
                allow_credentials.append({
                    "type": "public-key",
                    "id": base64.b64encode(credential_id).decode(),  # Convert bytes to base64 string
                    "transports": ["internal", "hybrid"]
                })
            except Exception as e:
                print(f"Error processing user passkey: {str(e)}")
                return jsonify({
                    'error': 'Invalid passkey data. Please register a new passkey.'
                }), 400
        else:
            # If no email provided, get all registered passkeys
            users_with_passkeys = User.query.filter(
                User.passkey_credential_id.isnot(None),
                User.passkey_public_key.isnot(None)
            ).all()
            
            if not users_with_passkeys:
                return jsonify({
                    'error': 'No registered passkeys found. Please register a passkey first.'
                }), 400
            
            # Create allow_credentials list for all registered passkeys
            for user in users_with_passkeys:
                try:
                    credential_id = base64url_to_bytes(user.passkey_credential_id)
                    allow_credentials.append({
                        "type": "public-key",
                        "id": base64.b64encode(credential_id).decode(),  # Convert bytes to base64 string
                        "transports": ["internal", "hybrid"]
                    })
                except Exception as e:
                    print(f"Error processing user {user.id} passkey: {str(e)}")
                    continue
        
        if not allow_credentials:
            return jsonify({
                'error': 'No valid passkeys found. Please register a new passkey.'
            }), 400
            
        try:
            print("Generating authentication options with credentials:", allow_credentials)
            
            # Generate random challenge
            challenge = os.urandom(32)
            challenge_b64 = base64.b64encode(challenge).decode()  # Convert challenge to base64 string
            
            # Create authentication options
            options = {
                "challenge": challenge_b64,
                "timeout": 30000,
                "rpId": "localhost",
                "allowCredentials": allow_credentials,
                "userVerification": "preferred"
            }
            
            # Store challenge in session
            session['auth_challenge'] = challenge_b64
            session['auth_timeout'] = datetime.utcnow().timestamp() + 30
            
            print("Generated options:", json.dumps(options, indent=2))
            return jsonify(options)
            
        except Exception as e:
            print(f"Error generating authentication options: {str(e)}")
            return jsonify({
                'error': f'Failed to generate authentication options: {str(e)}'
            }), 500
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return jsonify({
            'error': 'Authentication failed. Please try again.'
        }), 500

@bp.route('/passkey/authenticate/verify', methods=['POST'])
@csrf.exempt
def verify_passkey_authentication():
    """Verify passkey authentication attempt."""
    try:
        # Check timeout
        timeout = session.get('auth_timeout')
        if not timeout or datetime.utcnow().timestamp() > timeout:
            return jsonify({
                'error': 'Authentication timeout. Please try again.'
            }), 400

        # Get challenge from session
        challenge = session.get('auth_challenge')
        if not challenge:
            return jsonify({
                'error': 'Invalid session state. Please try again.'
            }), 400

        try:
            # Parse the authentication response
            data = request.get_json()
            print(f"Received authentication data: {json.dumps(data, indent=2)}")
            
            # Parse the credential using webauthn helper
            credential = parse_authentication_credential_json(json.dumps(data))
            print(f"Parsed credential object successfully")

        except Exception as e:
            print(f"Error parsing authentication data: {str(e)}")
            print(f"Raw data: {request.get_data(as_text=True)}")
            return jsonify({
                'error': f'Invalid authentication data: {str(e)}'
            }), 400

        try:
            # Find user by credential ID
            credential_id = base64.b64encode(credential.raw_id).decode()
            user = User.query.filter_by(passkey_credential_id=credential_id).first()
            
            if not user:
                return jsonify({
                    'error': 'No matching passkey found.'
                }), 400

            # Verify the authentication response
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=base64.b64decode(challenge),
                expected_rp_id="localhost",
                expected_origin=request.url_root.rstrip('/'),
                credential_public_key=base64url_to_bytes(user.passkey_public_key),
                credential_current_sign_count=user.passkey_sign_count,
                require_user_verification=True
            )
            print(f"Verification successful: {verification}")

            # Update sign count
            user.passkey_sign_count = verification.new_sign_count
            db.session.commit()

            # Log the user in
            login_user(user, remember=True)
            return jsonify({'status': 'success'})

        except Exception as e:
            print(f"Authentication verification error: {str(e)}")
            return jsonify({
                'error': f'Authentication verification failed: {str(e)}'
            }), 400

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return jsonify({
            'error': 'Authentication failed. Please try again.'
        }), 400

@bp.route('/passkey/remove', methods=['POST'])
@login_required
@csrf.exempt
def remove_passkey():
    """Remove registered passkey from user account."""
    try:
        if not current_user.has_passkey():
            return jsonify({
                'error': 'No passkey found for your account.'
            }), 400
            
        current_user.remove_passkey()
        db.session.commit()
        
        flash('Passkey removed successfully.', 'success')
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error removing passkey: {str(e)}")
        return jsonify({
            'error': 'Failed to remove passkey. Please try again.'
        }), 500

@bp.route('/passkey/status')
@login_required
def passkey_status():
    """Get current user's passkey status."""
    try:
        return jsonify({
            'status': 'success',
            'has_passkey': current_user.has_passkey(),
            'email': current_user.email
        })
    except Exception as e:
        print(f"Error getting passkey status: {str(e)}")
        return jsonify({
            'error': 'Failed to get passkey status.'
        }), 500

@bp.route('/profile')
@login_required
def profile():
    """User profile and account settings page."""
    return render_template('auth/profile.html')
