from flask import Blueprint, render_template, flash, redirect, request, jsonify, abort
import logging
from functools import wraps
from .models import Cart, Order, Category, Product, Wishlist
from flask_login import login_required, current_user
from . import db
import requests


views = Blueprint('views', __name__)

KHALTI_SECRET_KEY = "test_secret_key_xxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your actual test/live secret key
# Use a named constant for shipping fee
SHIPPING_FEE = 200

# Helper: Get current user's cart
def get_cart():
    if current_user.is_authenticated:
        return Cart.query.filter_by(customer_link=current_user.id).all()
    return []

# Helper: Validate cart_id input
def validate_cart_id(cart_id):
    if not cart_id or not str(cart_id).isdigit():
        abort(400, description="Invalid cart ID")
    return int(cart_id)

# Decorator: Enforce POST method for mutations
def post_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method != 'POST':
            abort(405)
        return f(*args, **kwargs)
    return decorated_function

@views.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True)
    category = Category.query.all()
    return render_template('home.html', items=items, categories=category,
                           cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@views.route('/product')
def product():
    items = Product.query.filter_by()
    category = Category.query.all()
    return render_template('product.html', items=items, categories=category,
                           cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@views.route('/product/<int:item_id>')
def product_detail(item_id):
    product = Product.query.filter_by(id=item_id).first_or_404()
    return render_template('product_detail.html', product=product)

@views.route('/add-to-cart/<int:item_id>', methods=['POST'])
@login_required
@post_required
def add_to_cart(item_id):
    """Add product to cart. Uses POST for security."""
    item_to_add = Product.query.get_or_404(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    try:
        if item_exists:
            item_exists.quantity += 1
            db.session.commit()
            flash(f'Quantity of {item_exists.product.product_name} updated')
        else:
            new_cart_item = Cart(quantity=1, product_link=item_to_add.id, customer_link=current_user.id)
            db.session.add(new_cart_item)
            db.session.commit()
            flash(f'{new_cart_item.product.product_name} added to cart')
    except Exception as e:
        logging.error(f'Add to cart error: {e}')
        flash('Item could not be added')
    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()

    # subtotal = sum of product price × quantity
    subtotal = sum(item.product.current_price * item.quantity for item in cart)

    # for now we keep delivery/discount static
    delivery = 0
    discount = 10  # or calculate dynamically

    total = subtotal + delivery - discount

    return render_template(
        'cart_view.html',
        cart=cart,
        subtotal=subtotal,
        delivery=delivery,
        discount=discount,
        total=total
    )


@views.route('/update-cart/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    data = request.get_json()
    new_quantity = data.get('quantity')

    # Fixed: Use customer_link instead of customer_id to match your model
    cart_item = Cart.query.filter_by(id=item_id, customer_link=current_user.id).first()
    print(f"Cart item found: {cart_item}")
    
    if not cart_item:
        return {"error": "Item not found"}, 404

    try:
        new_quantity = int(new_quantity)
        if new_quantity < 1:
            return {"error": "Quantity must be at least 1"}, 400
    except (ValueError, TypeError):
        return {"error": "Invalid quantity"}, 400

    cart_item.quantity = new_quantity
    db.session.commit()

    # recalc totals for the whole cart
    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
    subtotal = sum(i.product.current_price * i.quantity for i in cart_items)
    
    # Calculate total cart count (total quantity of all items)
    cart_count = sum(i.quantity for i in cart_items)
    # OR if you want unique item count: cart_count = len(cart_items)
    
    delivery = 0
    discount = 10
    total = subtotal + delivery - discount

    return {
        "item_total": cart_item.product.current_price * cart_item.quantity,
        "subtotal": subtotal,
        "delivery": delivery,
        "discount": discount,
        "total": total,
        "cart_count": cart_count  # Add this
    }

# Additional routes for complete functionality
@views.route('/remove-cart-item/<int:item_id>', methods=['DELETE'])
@login_required
def remove_cart_item(item_id):
    cart_item = Cart.query.filter_by(id=item_id, customer_link=current_user.id).first()
    
    if not cart_item:
        return {"error": "Item not found"}, 404
    
    db.session.delete(cart_item)
    db.session.commit()
    
    # Check if cart is empty
    remaining_items = Cart.query.filter_by(customer_link=current_user.id).all()
    cart_empty = len(remaining_items) == 0
    
    if cart_empty:
        return {
            "success": True,
            "cart_empty": True,
            "subtotal": 0,
            "delivery": 0,
            "discount": 0,
            "total": 0
        }
    
    # Recalculate totals
    subtotal = sum(i.product.current_price * i.quantity for i in remaining_items)
    delivery = 0
    discount = 10
    total = subtotal + delivery - discount
    
    return {
        "success": True,
        "cart_empty": False,
        "subtotal": subtotal,
        "delivery": delivery,
        "discount": discount,
        "total": total
    }

@views.route('/clear-cart', methods=['POST'])
@login_required
def clear_cart():
    try:
        Cart.query.filter_by(customer_link=current_user.id).delete()
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        return {"error": "Failed to clear cart"}, 500

@views.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    data = request.get_json()
    coupon_code = data.get('coupon_code', '').strip().upper()
    
    if not coupon_code:
        return {"error": "Please enter a coupon code"}, 400
    
    # Calculate current totals
    cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
    if not cart_items:
        return {"error": "Your cart is empty"}, 400
        
    subtotal = sum(i.product.current_price * i.quantity for i in cart_items)
    delivery = 0
    
    # Simple coupon logic - you can expand this
    discount = 10  # default
    if coupon_code == 'SAVE20':
        discount = 20
    elif coupon_code == 'SAVE50':
        discount = 50
    elif coupon_code == 'FREESHIP':
        discount = 10
        delivery = 0
    else:
        return {"error": "Invalid coupon code"}, 400
    
    total = subtotal + delivery - discount
    
    return {
        "success": True,
        "subtotal": subtotal,
        "delivery": delivery,
        "discount": discount,
        "total": total,
        "message": f"Coupon {coupon_code} applied successfully!"
    }



@views.route('/pluscart', methods=['POST'])
@login_required
@post_required
def plus_cart():
    """Increase cart item quantity. Uses POST."""
    cart_id = request.form.get('cart_id')
    cart_id = validate_cart_id(cart_id)
    cart_item = Cart.query.get_or_404(cart_id)
    cart_item.quantity += 1
    db.session.commit()
    return _cart_amount_json()

@views.route('/minuscart', methods=['POST'])
@login_required
@post_required
def minus_cart():
    """Decrease cart item quantity. Uses POST."""
    cart_id = request.form.get('cart_id')
    cart_id = validate_cart_id(cart_id)
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        db.session.commit()
    return _cart_amount_json()

@views.route('/removecart', methods=['POST'])
@login_required
@post_required
def remove_cart():
    """Remove item from cart. Uses POST."""
    cart_id = request.form.get('cart_id')
    cart_id = validate_cart_id(cart_id)
    cart_item = Cart.query.get_or_404(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    return _cart_amount_json()

def _cart_amount_json():
    """Return cart summary as JSON."""
    cart = get_cart()
    amount = sum(item.product.current_price * item.quantity for item in cart)
    return jsonify({
        'quantity': sum(item.quantity for item in cart),
        'amount': amount,
        'total': amount + SHIPPING_FEE
    })

@views.route('/verify-khalti', methods=['POST'])
@login_required
def verify_khalti():
    try:
        data = request.get_json()
        token = data.get('token')
        amount = data.get('amount')

        # Verify with Khalti
        headers = {
            "Authorization": f"Key {KHALTI_SECRET_KEY}"
        }
        payload = {
            "token": token,
            "amount": amount
        }

        response = requests.post("https://khalti.com/api/v2/payment/verify/", data=payload, headers=headers)

        if response.status_code == 200 and response.json().get('idx'):
            # Payment successful
            customer_cart = Cart.query.filter_by(customer_link=current_user.id).all()
            for item in customer_cart:
                new_order = Order(
                    quantity=item.quantity,
                    price=item.product.current_price,
                    status='Paid',
                    payment_id=token,
                    product_link=item.product_link,
                    customer_link=item.customer_link
                )
                db.session.add(new_order)
                product = Product.query.get(item.product_link)
                product.in_stock -= item.quantity
                db.session.delete(item)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False})
    except Exception as e:
            logging.error(f"Khalti verification error: {e}")
            return jsonify({'success': False})
    



@views.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(customer_id=current_user.id).all()
    wishlist_count = len(wishlist_items)
    return render_template('wishlist.html', wishlist_items=wishlist_items, wishlist_count=wishlist_count)
    

@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('orders.html', orders=orders)

@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items,
                               cart=Cart.query.filter_by(customer_link=current_user.id).all()
                               if current_user.is_authenticated else [])
    return render_template('search.html')


@views.route('/contact', methods=['GET'])
def contact():
    logging.info("Contact page accessed")
    return render_template('contact.html')