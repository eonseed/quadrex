from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.auth import bp
from app.models import User
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential
)
import base64
import json

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

@bp.route('/passkey/register', methods=['POST'])
@login_required
def register_passkey():
    """Generate options for registering a new passkey."""
    options = generate_registration_options(
        rp_name="Quadrex",
        rp_id=request.host.split(':')[0],
        user_id=str(current_user.id).encode('utf-8'),  # Convert to bytes
        user_name=current_user.email,
        user_display_name=current_user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED
        )
    )
    
    # Store challenge for verification
    session['register_challenge'] = options.challenge
    
    return jsonify(options_to_json(options))

@bp.route('/passkey/register/verify', methods=['POST'])
@login_required
def verify_passkey_registration():
    """Verify and store the newly created passkey."""
    try:
        credential = RegistrationCredential.parse_raw(request.get_data())
        verification = verify_registration_response(
            credential=credential,
            expected_challenge=session.pop('register_challenge'),
            expected_rp_id=request.host.split(':')[0],
            expected_origin=request.url_root.rstrip('/')
        )
        
        current_user.set_passkey(
            credential_id=base64.b64encode(credential.raw_id).decode('utf-8'),
            public_key=base64.b64encode(verification.credential_public_key).decode('utf-8')
        )
        db.session.commit()
        
        flash('Passkey registered successfully!', 'success')
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/passkey/authenticate', methods=['POST'])
def passkey_authenticate():
    """Generate options for passkey authentication."""
    email = request.json.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.has_passkey():
        return jsonify({'error': 'User not found or passkey not registered'}), 400
    
    try:
        credential_id = base64url_to_bytes(user.passkey_credential_id)
        options = generate_authentication_options(
            rp_id=request.host.split(':')[0],
            allow_credentials=[{
                'type': 'public-key',
                'id': credential_id,
            }],
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Store challenge and user ID for verification
        session['auth_challenge'] = options.challenge
        session['auth_user_id'] = user.id
        
        return jsonify(options_to_json(options))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/passkey/authenticate/verify', methods=['POST'])
def verify_passkey_authentication():
    """Verify passkey authentication attempt."""
    try:
        credential = AuthenticationCredential.parse_raw(request.get_data())
        user_id = session.pop('auth_user_id', None)
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=session.pop('auth_challenge'),
            expected_rp_id=request.host.split(':')[0],
            expected_origin=request.url_root.rstrip('/'),
            credential_public_key=base64url_to_bytes(user.passkey_public_key),
            credential_current_sign_count=user.passkey_sign_count
        )
        
        # Update sign count
        user.update_passkey_sign_count(verification.new_sign_count)
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash('Logged in successfully with passkey!', 'success')
        return jsonify({'status': 'success', 'redirect': url_for('main.index')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/passkey/status')
@login_required
def passkey_status():
    """Check if current user has a passkey registered."""
    return jsonify({
        'has_passkey': current_user.has_passkey()
    })

@bp.route('/profile')
@login_required
def profile():
    """User profile and account settings page."""
    return render_template('auth/profile.html')
