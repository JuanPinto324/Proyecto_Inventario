from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.models import Product, Sale, SaleItem
from app import db
from sqlalchemy import func


pos_bp = Blueprint('pos', __name__, url_prefix='/pos')


def _next_invoice():
    last = Sale.query.order_by(Sale.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f'FAC-{num:06d}'


@pos_bp.route('/')
@login_required
def index():
    # Todos los productos disponibles
    products = Product.query.filter(
        Product.is_active == True,
        Product.stock > 0
    ).order_by(Product.name).all()

    # Top 5 más vendidos
    top_ids = db.session.query(
        SaleItem.product_id,
        func.sum(SaleItem.quantity).label('total_vendido')
    ).group_by(SaleItem.product_id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(5).all()

    top_products = []
    for row in top_ids:
        p = Product.query.get(row.product_id)
        if p and p.is_active and p.stock > 0:
            top_products.append(p)

    return render_template('pos/index.html', products=products, top_products=top_products)


@pos_bp.route('/complete', methods=['POST'])
@login_required
def complete():
    data = request.get_json()

    customer_id    = data.get('customer_id', '').strip()
    customer_name  = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    customer_email = data.get('customer_email', '').strip()
    items          = data.get('items', [])

    if not customer_id or not customer_name:
        return jsonify({'ok': False, 'msg': 'Datos del cliente incompletos.'}), 400
    if not items:
        return jsonify({'ok': False, 'msg': 'El carrito está vacío.'}), 400

    total = 0
    validated = []
    for item in items:
        product = Product.query.get(item['product_id'])
        if not product or product.stock < item['quantity']:
            return jsonify({'ok': False, 'msg': f'Stock insuficiente para {item["name"]}.'}), 400
        subtotal = product.sell_price * item['quantity']
        total += subtotal
        validated.append((product, item['quantity'], product.sell_price, subtotal))

    sale = Sale(
        invoice_number=_next_invoice(),
        customer_id=customer_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        total=total,
        cashier_id=current_user.id
    )
    db.session.add(sale)
    db.session.flush()

    for product, qty, price, subtotal in validated:
        item_row = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=qty,
            unit_price=price,
            subtotal=subtotal
        )
        db.session.add(item_row)
        product.stock -= qty

    db.session.commit()
    return jsonify({'ok': True, 'sale_id': sale.id, 'invoice': sale.invoice_number})


@pos_bp.route('/ticket/<int:sale_id>')
@login_required
def ticket(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('pos/ticket.html', sale=sale)
