from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from app import db, bcrypt, login_manager


# Hora local Colombia
def colombia_now():
    return datetime.now(ZoneInfo("America/Bogota"))


# ──────────────────────────────────────────────────────────────────
# USER LOADER
# ──────────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ──────────────────────────────────────────────────────────────────
# USUARIO
# ──────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id             = db.Column(db.Integer, primary_key=True)
    full_name      = db.Column(db.String(120), nullable=False)
    identification = db.Column(db.String(30), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    role           = db.Column(db.String(20), nullable=False, default='cajero')
    # 'jefe' | 'administrador' | 'cajero'
    is_active      = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=colombia_now)

    # Relaciones
    sales = db.relationship('Sale', backref='cashier', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def role_color(self):
        colors = {'jefe': '#FFD700', 'administrador': '#E53E3E', 'cajero': '#718096'}
        return colors.get(self.role, '#718096')

    @property
    def role_label(self):
        labels = {'jefe': 'Jefe', 'administrador': 'Administrador', 'cajero': 'Cajero'}
        return labels.get(self.role, self.role.capitalize())

    def __repr__(self):
        return f'<User {self.full_name} [{self.role}]>'


# ──────────────────────────────────────────────────────────────────
# PRODUCTO
# ──────────────────────────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'

    id           = db.Column(db.Integer, primary_key=True)
    code         = db.Column(db.String(50), unique=True, nullable=False)
    name         = db.Column(db.String(120), nullable=False)
    cost_price   = db.Column(db.Integer, nullable=False, default=0)   # sin decimales
    sell_price   = db.Column(db.Integer, nullable=False, default=0)
    stock        = db.Column(db.Integer, nullable=False, default=0)
    min_stock    = db.Column(db.Integer, nullable=False, default=5)
    is_active    = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=colombia_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=colombia_now, onupdate=colombia_now)

    # Relaciones
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

    @property
    def status(self):
        if self.stock == 0:
            return 'Agotado'
        elif self.stock <= self.min_stock:
            return 'Bajo Stock'
        return 'Disponible'

    @property
    def status_class(self):
        if self.stock == 0:
            return 'status-out'
        elif self.stock <= self.min_stock:
            return 'status-low'
        return 'status-ok'

    def __repr__(self):
        return f'<Product {self.code} - {self.name}>'


# ──────────────────────────────────────────────────────────────────
# VENTA
# ──────────────────────────────────────────────────────────────────
class Sale(db.Model):
    __tablename__ = 'sales'

    id              = db.Column(db.Integer, primary_key=True)
    invoice_number  = db.Column(db.String(20), unique=True, nullable=False)
    customer_id     = db.Column(db.String(30), nullable=False)
    customer_name   = db.Column(db.String(120), nullable=False)
    customer_phone  = db.Column(db.String(20))
    customer_email  = db.Column(db.String(120))
    total           = db.Column(db.Integer, nullable=False, default=0)
    cashier_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=colombia_now)
    is_returned     = db.Column(db.Boolean, default=False)

    # Relaciones
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Sale {self.invoice_number} - ${self.total}>'


# ──────────────────────────────────────────────────────────────────
# ÍTEM DE VENTA
# ──────────────────────────────────────────────────────────────────
class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id          = db.Column(db.Integer, primary_key=True)
    sale_id     = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id  = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    unit_price  = db.Column(db.Integer, nullable=False)   # precio al momento de venta
    subtotal    = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<SaleItem sale={self.sale_id} product={self.product_id} qty={self.quantity}>'


# ──────────────────────────────────────────────────────────────────
# DEVOLUCIÓN
# ──────────────────────────────────────────────────────────────────
class Return(db.Model):
    __tablename__ = 'returns'

    id          = db.Column(db.Integer, primary_key=True)
    sale_id     = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    reason      = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=colombia_now)

    sale       = db.relationship('Sale', backref='returns')
    processor  = db.relationship('User', backref='returns_processed')

    def __repr__(self):
        return f'<Return sale={self.sale_id}>'
