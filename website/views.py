from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Cart, Order, Category, Product, Wishlist
from flask_login import login_required, current_user
from . import db
import requests


views = Blueprint('views', __name__)

KHALTI_SECRET_KEY = "test_secret_key_xxxxxxxxxxxxxxxxxxxxxxxx"  # Replace with your actual test/live secret key

@views.route('/')
def home():
    items = Product.query.filter_by(flash_sale=True)
    category = Category.query.all()
    return render_template('home.html', items=items, categories=category,
                           cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity += 1
            db.session.commit()
            flash(f'Quantity of {item_exists.product.product_name} updated')
            return redirect(request.referrer)
        except Exception as e:
            print('Quantity not updated:', e)
            flash('Failed to update quantity')
            return redirect(request.referrer)

    new_cart_item = Cart(quantity=1, product_link=item_to_add.id, customer_link=current_user.id)
    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} added to cart')
    except Exception as e:
        print('Add to cart error:', e)
        flash('Item could not be added')
    return redirect(request.referrer)

@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.product.current_price * item.quantity for item in cart)
    return render_template('cart.html', cart=cart, amount=amount, total=amount + 200)

@views.route('/pluscart')
@login_required
def plus_cart():
    cart_id = request.args.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    cart_item.quantity += 1
    db.session.commit()
    return _cart_amount_json()

@views.route('/minuscart')
@login_required
def minus_cart():
    cart_id = request.args.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    cart_item.quantity -= 1
    db.session.commit()
    return _cart_amount_json()

@views.route('/removecart')
@login_required
def remove_cart():
    cart_id = request.args.get('cart_id')
    cart_item = Cart.query.get(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    return _cart_amount_json()

def _cart_amount_json():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = sum(item.product.current_price * item.quantity for item in cart)
    return jsonify({
        'quantity': sum(item.quantity for item in cart),
        'amount': amount,
        'total': amount + 200
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
        print("Khalti verification error:", e)
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
