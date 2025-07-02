from flask import Blueprint, render_template, flash, redirect, request, url_for, abort
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import Customer, ContactMessage, Order, Wishlist, Product, Category
from . import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password1 = form.password1.data
        password2 = form.password2.data

        if password1 == password2:
            new_customer = Customer()
            new_customer.email = email
            new_customer.username = username
            new_customer.password = password2

            try:
                db.session.add(new_customer)
                db.session.commit()
                flash('Account Created Successfully, You can now Login')
                return redirect('/login')
            except Exception as e:
                print(e)
                flash('Account Not Created!!, Email already exists')

            form.email.data = ''
            form.username.data = ''
            form.password1.data = ''
            form.password2.data = ''

    return render_template('signup.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        customer = Customer.query.filter_by(email=email).first()

        if not customer:
            flash('Account does not exist. Please Sign Up.', 'danger')
            return render_template('login.html', form=form)

        if not customer.verify_password(password=password):
            flash('Incorrect Email or Password.', 'danger')
            return render_template('login.html', form=form)

        # Successful login
        login_user(customer)
        flash('Logged in successfully!', 'success')
        return redirect('/')

    return render_template('login.html', form=form)



@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect('/')


@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get(customer_id)
    print('Customer ID:', customer_id)
    return render_template('profile.html', customer=customer)


@auth.route('/change-password/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def change_password(customer_id):
    form = PasswordChangeForm()
    customer = Customer.query.get(customer_id)
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if customer.verify_password(current_password):
            if new_password == confirm_new_password:
                customer.password = confirm_new_password
                db.session.commit()
                flash('Password Updated Successfully')
                return redirect(f'/profile/{customer.id}')
            else:
                flash('New Passwords do not match!!')

        else:
            flash('Current Password is Incorrect')

    return render_template('change_password.html', form=form)





@auth.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Save the message to the database
        new_message = ContactMessage(name=name, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()
        
        flash('Your message has been sent!')
        return redirect('/contact')

    return render_template('contact.html')





from sqlalchemy.orm import joinedload


@auth.route('/products')
@login_required
def products():
    # This example assumes you have a Product model and template.
    products = Product.query.all()
    return render_template('products.html', products=products)



@auth.route('/about')
def about_us():
    return render_template('about_us.html')









@auth.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(customer_id=current_user.id).options(
        joinedload(Wishlist.product)
    ).all()
    return render_template('wishlist.html', wishlist_items=wishlist_items)


@auth.route('/add-to-wishlist/<int:item_id>', methods=['POST'])
@login_required
def add_to_wishlist(item_id):
    item = Product.query.get(item_id)  # Fetch the product by ID
    if not item:
        flash("Product not found.", "danger")
        return redirect(url_for('products'))  # Redirect to products page or an appropriate page
    
    # Check if the item is already in the wishlist
    existing_item = Wishlist.query.filter_by(customer_id=current_user.id, product_id=item.id).first()
    if existing_item:
        flash(f"'{item.product_name}' is already in your wishlist.", "info")
    else:
        # Add the item to the wishlist
        wishlist_item = Wishlist(customer_id=current_user.id, product_id=item.id, quantity=1)
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f"'{item.product_name}' added to your wishlist!", "success")
    
    return redirect(url_for('auth.wishlist'))  # Change 'auth.view_wishlist' to your wishlist view function name








from sqlalchemy.exc import SQLAlchemyError

@auth.route('/remove-from-wishlist/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    try:
        # Fetch the wishlist item by its ID
        wishlist_item = Wishlist.query.get_or_404(item_id)
        
        # Ensure the item belongs to the current user
        if wishlist_item.customer_id != current_user.id:
            flash("You are not authorized to remove this item.", "danger")
            return redirect(url_for('auth.wishlist'))  # Redirect to wishlist page
        
        # Delete the item from the wishlist
        db.session.delete(wishlist_item)
        db.session.commit()
        
        # Flash success message
        flash('Item successfully removed from your wishlist.', 'success')
        
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback in case of error
        flash(f"An error occurred while removing the item: {str(e)}", "danger")
    
    # Redirect back to the wishlist page
    return redirect(url_for('auth.wishlist'))



@auth.route('/category/<int:category_id>', methods=['GET'])
def filter_products_by_category(category_id):
    # Fetch the category by its ID
    category = Category.query.get_or_404(category_id)

    # Get all products belonging to this category
    products = Product.query.filter_by(category_id=category.id).all()

    # Render the template with the filtered products
    return render_template('filtered_products.html', category=category, products=products)



@auth.route('/delete-order/<int:order_id>')
def delete_order(order_id):
    order = Order.query.get(order_id)
    if order:
        db.session.delete(order)
        db.session.commit()
        flash('Order deleted successfully.', 'success')
    else:
        flash('Order not found.', 'danger')
    return redirect('/view-orders')


@auth.route('/delete-customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if customer.id == 3:
        flash("Admin account cannot be deleted.", "warning")
        return redirect(url_for('admin.display_customers'))

    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!", "success")
    return redirect(url_for('admin.display_customers'))  




