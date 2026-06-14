from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
import os, requests

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        identification   = request.form.get('identification', '').strip()
        password         = request.form.get('password', '')
        #turnstile_token  = request.form.get('cf-turnstile-response', '')

        # Verificar Turnstile con Cloudflare
        secret_key = os.environ.get('TURNSTILE_SECRET_KEY', '')
        verify_resp = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={
                'secret': secret_key,
                'response': turnstile_token,
                'remoteip': request.remote_addr
            }
        )
        result = verify_resp.json()

        if not result.get('success'):
            flash('Verificación de seguridad fallida. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(identification=identification, is_active=True).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Bienvenido, {user.full_name}.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or _redirect_by_role(user.role, as_url=True))
        else:
            flash('Identificación o contraseña incorrecta.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()

    # Limpiar CAPTCHA al cerrar sesión
    session.pop('captcha_answer', None)
    session.pop('captcha_question', None)

    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role(role, as_url=False):
    dest = 'dashboard.index' if role in ('jefe', 'administrador') else 'pos.index'
    return url_for(dest) if as_url else redirect(url_for(dest))
