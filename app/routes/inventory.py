from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Product
from app import db
from functools import wraps
from flask import abort

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('jefe', 'administrador'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _next_product_code():
    """Encuentra el primer código PROD-XXX disponible en la secuencia."""
    all_products = Product.query.filter(Product.code.like('PROD-%')).all()

    used_numbers = set()
    for p in all_products:
        try:
            num = int(p.code.split('-')[1])
            used_numbers.add(num)
        except (ValueError, IndexError):
            pass

    i = 1
    while i in used_numbers:
        i += 1

    return f'PROD-{i:03d}'


@inventory_bp.route('/')
@login_required
@admin_required
def index():
    q = request.args.get('q', '').strip()
    query = Product.query.filter_by(is_active=True)
    if q:
        query = query.filter(
            (Product.name.ilike(f'%{q}%')) | (Product.code.ilike(f'%{q}%'))
        )
    products = query.order_by(Product.name).all()
    return render_template('inventory/index.html', products=products, q=q)


@inventory_bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new():
    if request.method == 'POST':
        code       = request.form.get('code', '').strip().upper()
        name       = request.form.get('name', '').strip()
        cost_price = int(request.form.get('cost_price', 0))
        sell_price = int(request.form.get('sell_price', 0))
        stock      = int(request.form.get('stock', 0))
        min_stock  = int(request.form.get('min_stock', 5))

        existing_product = Product.query.filter_by(code=code).first()

        if existing_product:
            if not existing_product.is_active:
                existing_product.name       = name
                existing_product.cost_price = cost_price
                existing_product.sell_price = sell_price
                existing_product.stock      = stock
                existing_product.min_stock  = min_stock
                existing_product.is_active  = True
                db.session.commit()
                flash(f'Producto "{name}" restaurado exitosamente.', 'success')
                return redirect(url_for('inventory.index'))

            flash('Ya existe un producto con ese código.', 'danger')
            return redirect(url_for('inventory.new'))

        product = Product(
            code=code, name=name,
            cost_price=cost_price, sell_price=sell_price,
            stock=stock, min_stock=min_stock
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Producto "{name}" registrado exitosamente.', 'success')
        return redirect(url_for('inventory.index'))

    suggested_code = _next_product_code()
    return render_template('inventory/form.html', product=None, action='Nuevo',
                           suggested_code=suggested_code)


@inventory_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name       = request.form.get('name', '').strip()
        product.cost_price = int(request.form.get('cost_price', 0))
        product.sell_price = int(request.form.get('sell_price', 0))
        product.stock      = int(request.form.get('stock', 0))
        product.min_stock  = int(request.form.get('min_stock', 5))
        db.session.commit()
        flash('Producto actualizado.', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/form.html', product=product, action='Editar')


@inventory_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = False
    db.session.commit()
    flash(f'Producto "{product.name}" eliminado.', 'warning')
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/api/search')
@login_required
def api_search():
    """Endpoint JSON para el POS."""
    q = request.args.get('q', '').strip()
    products = Product.query.filter(
        Product.is_active == True,
        Product.stock > 0,
        (Product.name.ilike(f'%{q}%')) | (Product.code.ilike(f'%{q}%'))
    ).limit(10).all()
    return jsonify([{
        'id': p.id, 'code': p.code, 'name': p.name,
        'sell_price': p.sell_price, 'stock': p.stock
    } for p in products])
    