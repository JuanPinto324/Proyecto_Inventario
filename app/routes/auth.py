from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    if request.method == 'POST':
        identification = request.form.get('identification', '').strip()
        password = request.form.get('password', '')
        captcha_answer = request.form.get('captcha_answer', '')
        captcha_expected = session.get('captcha_answer')


        # Validar CAPTCHA
        if not captcha_answer or str(captcha_answer) != str(captcha_expected):
            flash('Respuesta del CAPTCHA incorrecta.', 'danger')

            # Eliminar CAPTCHA actual para generar uno nuevo
            session.pop('captcha_answer', None)
            session.pop('captcha_question', None)

            return redirect(url_for('auth.login'))

        user = User.query.filter_by(
            identification=identification,
            is_active=True
        ).first()

        if user and user.check_password(password):

            # Limpiar CAPTCHA después de login exitoso
            session.pop('captcha_answer', None)
            session.pop('captcha_question', None)

            login_user(user)
            flash(f'Bienvenido, {user.full_name}.', 'success')

            next_page = request.args.get('next')
            return redirect(
                next_page or _redirect_by_role(user.role, as_url=True)
            )

        else:
            flash('Identificación o contraseña incorrecta.', 'danger')

            # Generar nuevo CAPTCHA si las credenciales son incorrectas
            session.pop('captcha_answer', None)
            session.pop('captcha_question', None)

            return redirect(url_for('auth.login'))

    # Generar CAPTCHA solo si no existe uno en sesión
    import random

    if (
        'captcha_answer' not in session or
        'captcha_question' not in session
    ):
        a = random.randint(1, 9)
        b = random.randint(1, 9)

        session['captcha_answer'] = a + b
        session['captcha_question'] = f'{a} + {b} = ?'

    captcha_question = session.get('captcha_question')

    return render_template(
        'auth/login.html',
        captcha_question=captcha_question
    )


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
