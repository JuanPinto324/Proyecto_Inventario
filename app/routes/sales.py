from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Sale, SaleItem, Return, Product
from app import db
from datetime import timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import func
import datetime
from functools import wraps
from flask import abort

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('jefe', 'administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


@sales_bp.route('/')
@login_required
@admin_required
def index():
    filter_type = request.args.get('filter', 'today')
    date_from   = request.args.get('from', '')
    date_to     = request.args.get('to', '')
    
    from zoneinfo import ZoneInfo
    from datetime import datetime, timedelta
    bogota = ZoneInfo("America/Bogota")
    now_bogota = datetime.now(bogota)
    today = now_bogota.date()

    query = Sale.query
    if filter_type == 'today':
        # Convertir inicio y fin del día Colombia a UTC para comparar con la BD
        start = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=bogota)
        end   = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=bogota)
        query = query.filter(Sale.created_at >= start, Sale.created_at <= end)
    elif filter_type == 'yesterday':
        yesterday = today - timedelta(days=1)
        start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0, tzinfo=bogota)
        end   = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=bogota)
        query = query.filter(Sale.created_at >= start, Sale.created_at <= end)
    elif filter_type == 'range' and date_from and date_to:
        query = query.filter(
            func.date(Sale.created_at) >= date_from,
            func.date(Sale.created_at) <= date_to
        )

    sales = query.order_by(Sale.created_at.desc()).all()

    total_amount   = sum(s.total for s in sales if not s.is_returned)
    total_invoices = len([s for s in sales if not s.is_returned])
    total_items    = sum(
        sum(i.quantity for i in s.items) for s in sales if not s.is_returned
    )
    total_returns  = len([s for s in sales if s.is_returned])

    return render_template('sales/index.html',
        sales=sales,
        total_amount=total_amount,
        total_invoices=total_invoices,
        total_items=total_items,
        total_returns=total_returns,
        filter_type=filter_type,
        date_from=date_from,
        date_to=date_to
    )


@sales_bp.route('/<int:sale_id>')
@login_required
@admin_required
def detail(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales/detail.html', sale=sale)


@sales_bp.route('/<int:sale_id>/return', methods=['POST'])
@login_required
@admin_required
def process_return(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if sale.is_returned:
        flash('Esta venta ya fue devuelta.', 'warning')
        return redirect(url_for('sales.detail', sale_id=sale_id))

    reason = request.form.get('reason', '').strip()

    # Restaurar stock
    for item in sale.items:
        item.product.stock += item.quantity

    sale.is_returned = True
    ret = Return(sale_id=sale.id, reason=reason, processed_by=current_user.id)
    db.session.add(ret)
    db.session.commit()

    flash(f'Devolución de la factura {sale.invoice_number} procesada.', 'success')
    return redirect(url_for('sales.detail', sale_id=sale_id))
