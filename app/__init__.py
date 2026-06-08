import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pycommercex-dev-secret-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:///pycommercex.db'
    )
    # Render usa postgres://, SQLAlchemy necesita postgresql://
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config[
            'SQLALCHEMY_DATABASE_URI'
        ].replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Extensiones ────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para continuar.'
    login_manager.login_message_category = 'warning'

    # ── Filtro de zona horaria Colombia ────────────────────────────
    from zoneinfo import ZoneInfo
    from datetime import timezone as tz_utc

    @app.template_filter('col_time')
    def col_time_filter(dt):
        if dt is None:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_utc.utc)
        return dt.astimezone(ZoneInfo("America/Bogota")).strftime('%d/%m/%Y %H:%M')

    # ── Blueprints ─────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.inventory import inventory_bp
    from app.routes.pos import pos_bp
    from app.routes.sales import sales_bp
    from app.routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(users_bp)

    # ── Crear tablas + usuario jefe inicial ───────────────────────
    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    """Crea el usuario Jefe por defecto si no existe ninguno."""
    from app.models import User
    if User.query.count() == 0:
        jefe = User(
            full_name='Administrador Principal',
            identification='0000000000',
            role='jefe',
            is_active=True
        )
        jefe.set_password('admin123')
        db.session.add(jefe)
        db.session.commit()
        print('[PyCommerceX] Usuario jefe creado → ID: 0000000000 | Pass: admin123')