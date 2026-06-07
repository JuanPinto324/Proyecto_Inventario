from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User
from app import db
from functools import wraps
from flask import abort

users_bp = Blueprint('users', __name__, url_prefix='/users')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('jefe', 'administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _allowed_roles_for(current_role):
    """Roles que puede crear/editar el usuario actual."""
    if current_role == 'jefe':
        return ['jefe', 'administrador', 'cajero']
    return ['cajero']


@users_bp.route('/')
@login_required
@admin_required
def index():
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    return render_template('users/index.html', users=users)


@users_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new():
    allowed = _allowed_roles_for(current_user.role)

    if request.method == 'POST':
        full_name      = request.form.get('full_name', '').strip()
        identification = request.form.get('identification', '').strip()
        password       = request.form.get('password', '')
        role           = request.form.get('role', 'cajero')

        if role not in allowed:
            flash('No tienes permiso para crear usuarios con ese rol.', 'danger')
            return redirect(url_for('users.new'))

        if User.query.filter_by(identification=identification).first():
            flash('Ya existe un usuario con esa identificación.', 'danger')
            return redirect(url_for('users.new'))

        user = User(full_name=full_name, identification=identification, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario "{full_name}" creado exitosamente.', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=None, action='Nuevo', allowed_roles=allowed)


@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    user = User.query.get_or_404(user_id)
    allowed = _allowed_roles_for(current_user.role)

    # Administrador no puede editar jefes ni otros admins
    if current_user.role == 'administrador' and user.role != 'cajero':
        flash('No tienes permiso para editar este usuario.', 'danger')
        return redirect(url_for('users.index'))

    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        new_role = request.form.get('role', user.role)
        if new_role in allowed:
            user.role = new_role
        new_pass = request.form.get('password', '').strip()
        if new_pass:
            user.set_password(new_pass)
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', user=user, action='Editar', allowed_roles=allowed)


@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('users.index'))

    if current_user.role == 'administrador' and user.role != 'cajero':
        flash('No tienes permiso para eliminar este usuario.', 'danger')
        return redirect(url_for('users.index'))

    user.is_active = False
    db.session.commit()
    flash(f'Usuario "{user.full_name}" eliminado.', 'warning')
    return redirect(url_for('users.index'))
