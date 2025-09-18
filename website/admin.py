from flask import Blueprint, render_template, flash, send_from_directory, redirect,request, url_for
from flask_login import login_required, current_user
from .forms import ShopItemsForm, OrderForm
from werkzeug.utils import secure_filename
from .models import Product, Order, Customer, ContactMessage, Wishlist, Product
from . import db
from datetime import datetime
import os


admin= Blueprint('admin', __name__)
@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)



# @admin.route('/admin-page', endpoint='admin_page_unique')
# @login_required
# def admin_page():
#     if current_user.id == 3:  # Admin check
#         return render_template('admin.html')
#     return render_template('404.html')

    


@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    if current_user.id == 3:
        form = ShopItemsForm()

        if form.validate_on_submit():
            product_name = form.product_name.data
            current_price = form.current_price.data
            previous_price = form.previous_price.data
            in_stock = form.in_stock.data
            flash_sale = form.flash_sale.data
            category_id = form.category_id.data  # Get the selected category ID
            
            file = form.product_picture.data
            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'
            file.save(file_path)

            new_shop_item = Product()
            new_shop_item.product_name = product_name
            new_shop_item.current_price = current_price
            new_shop_item.previous_price = previous_price
            new_shop_item.in_stock = in_stock
            new_shop_item.flash_sale = flash_sale
            new_shop_item.product_picture = file_path
            new_shop_item.category_id = category_id  # Assign the category_id here
            
            try:
                db.session.add(new_shop_item)
                db.session.commit()
                flash(f'{product_name} added successfully', 'success')
                return render_template('add_shop_items.html', form=form)
            
            except Exception as e:
                print(e)
                flash('Item not added due to an error.', 'danger')
                return render_template('add_shop_items.html', form=form)
        
        return render_template('add_shop_items.html', form=form)
    
    return render_template('404.html')





@admin.route('/shop-items', methods=['GET', 'POST'])
@login_required
def shop_items():
    try:
        if current_user.id == 3:  # Admin check
            items = Product.query.order_by(Product.date_added).all()
            print(items)  # Debug: Log items to verify query results
            return render_template('shop_items.html', items=items)
        else:
            print("Unauthorized access. Current user ID:", current_user.id)  # Debug: Log user ID
            return render_template('404.html')
    except Exception as e:
        print("Error in /shop-items route:", e)  # Debug: Log any exceptions
        return render_template('404.html')

        
@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    if current_user.id == 3:  # Admin check
        item_to_update = Product.query.get_or_404(item_id)
        form = ShopItemsForm(obj=item_to_update)
        form.category_id.data = item_to_update.category_id

        if form.validate_on_submit():
            # Form data
            item_to_update.product_name = form.product_name.data
            item_to_update.current_price = form.current_price.data
            item_to_update.previous_price = form.previous_price.data
            item_to_update.in_stock = form.in_stock.data
            item_to_update.flash_sale = form.flash_sale.data
            item_to_update.category_id = form.category_id.data

            # Handle file upload
            file = form.product_picture.data
            if file and hasattr(file, 'filename') and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join('media', filename)
                file.save(file_path)
                item_to_update.product_picture = file_path
            # else: retain existing image (already in item_to_update.product_picture)

            try:
                db.session.commit()
                flash('Product updated successfully!', 'success')
                return redirect('/shop-items')
            except Exception as e:
                db.session.rollback()
                print("Error:", e)
                flash('Error updating product. Please try again.', 'danger')

        return render_template('update_item.html', form=form)

    return render_template('404.html')


@admin.route('/delete-item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    if current_user.id == 3:  # Admin check
        try:
            item_to_delete = Product.query.get_or_404(item_id)
            print(f"Product to delete: {item_to_delete}")  # Debugging

            # Check if any orders are linked to this product
            related_orders = Order.query.filter_by(product_link=item_id).all()
            if related_orders:
                print(f"Found related orders: {related_orders}")
                # Update the orders to set product_link to NULL
                Order.query.filter_by(product_link=item_id).update({"product_link": None})
                db.session.commit()
                print("Related orders updated to NULL.")

            # Now delete the product
            db.session.delete(item_to_delete)
            db.session.commit()

            flash("Item deleted successfully!", "success")
            print(f"Product {item_id} deleted.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting product: {str(e)}")  # Log the full error
            flash("Failed to delete item.", "danger")
        return redirect(url_for('admin.shop_items'))
    else:
        print(f"Unauthorized access by user ID: {current_user.id}")  # Debugging
        return render_template('404.html')


@admin.route('/view-orders')
@login_required
def order_view():
    if current_user.id == 3:
        orders = Order.query.all()
        return render_template('view_orders.html', orders=orders)
    return render_template('404.html')



@admin.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order(order_id):
    if current_user.id == 3:
        form = OrderForm()
        
        order= Order.query.get(order_id)
        if form.validate_on_submit():
            status= form.order_status.data
            order.status= status
            
            try:
                db.session.commit()
                flash(f'Order {order_id} updated successfully')
                return redirect('/view-orders')
            except Exception as e:
                print(e)
                flash (f'Order {order_id} not updated')
                return redirect ('/view-orders')
                
            
            

        return render_template('order_update.html', form=form)

    return render_template('404.html')




@admin.route('/customers')
@login_required
def display_customers():
    if current_user.id == 3:
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)
    return render_template('404.html')
        


@admin.route('/view-messages')
@login_required
def view_messages():
    if current_user.id == 3:
        messages = ContactMessage.query.order_by(ContactMessage.date_submitted.desc()).all()

        # Get today's date
        today = datetime.now().date()

        # Filter messages submitted today
        today_messages = [msg for msg in messages if msg.date_submitted.date() == today]

        return render_template('view_messages.html', messages=messages, today_messages=today_messages)
    
    return render_template('404.html')

@admin.route('/delete-message/<int:message_id>', methods=['POST'])
@login_required
def delete_message(message_id):
    if current_user.id != 3:
        return render_template('404.html')  # Only admin can delete

    message = ContactMessage.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted successfully.", "success")
    return redirect(url_for('admin.view_messages'))



        
@admin.route('/admin-page')
@login_required
def admin_page():
    if current_user.id == 3:
        return render_template('admin.html')
    return render_template('404.html')



@admin.route('/display-reviews', methods=['GET'])
def display_reviews():
    # Fetch the most recent 5 contact messages
    reviews = ContactMessage.query.order_by(ContactMessage.date_submitted.desc()).limit(5).all()
    
    return render_template('display_reviews.html', reviews=reviews)


@admin.route('/wishlist')
@login_required
def wishlist():
    try:
        # Fetch wishlist items for the current user
        wishlist_items = Wishlist.query.filter_by(customer_id=current_user.id).all()
        return render_template('wishlist.html', wishlist_items=wishlist_items)
    except Exception as e:
        # Log the error
        print(f"Error fetching wishlist: {e}")
        return "An error occurred while fetching the wishlist.", 500






