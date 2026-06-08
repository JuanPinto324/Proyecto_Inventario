from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem
from app import db
from sqlalchemy import func
from zoneinfo import ZoneInfo
import datetime
from functools import wraps
from flask import abort

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('jefe', 'administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/')
@login_required
@admin_required
def index():
    today = datetime.datetime.now(ZoneInfo("America/Bogota")).date()

    # Ventas del día
    sales_today = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.is_returned == False
    ).all()
    total_today   = sum(s.total for s in sales_today)
    invoices_today = len(sales_today)

    # Artículos vendidos hoy
    items_today = db.session.query(func.sum(SaleItem.quantity)).join(Sale).filter(
        func.date(Sale.created_at) == today,
        Sale.is_returned == False
    ).scalar() or 0

    # Productos
    total_products   = Product.query.filter_by(is_active=True).count()
    low_stock_prods  = Product.query.filter(
        Product.is_active == True,
        Product.stock > 0,
        Product.stock <= Product.min_stock
    ).all()
    out_of_stock     = Product.query.filter_by(is_active=True, stock=0).all()

    alert_products = low_stock_prods + out_of_stock

    return render_template('dashboard/index.html',
        total_today=total_today,
        invoices_today=invoices_today,
        items_today=items_today,
        total_products=total_products,
        low_stock_count=len(low_stock_prods),
        out_of_stock_count=len(out_of_stock),
        alert_products=alert_products
    )
