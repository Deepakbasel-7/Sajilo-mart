from . import db
from flask_login import UserMixin
from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash


class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(150))
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    cart_items = db.relationship(
        'Cart', backref=db.backref('customer', lazy=True), cascade="all, delete-orphan"
    )
    orders = db.relationship(
        'Order', backref=db.backref('customer', lazy=True), cascade="all, delete-orphan"
    )
    # wishlist_items = db.relationship(
    #     'Wishlist', backref=db.backref('customer', lazy=True), cascade="all, delete-orphan"
    #     )

    
    # Using property decorator for password
    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password= password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password= password)
    
    def __str__(self):
        return f'<Customer {self.id}>'

    

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)  # Relationship to Product

    def __repr__(self):
        return f"<Category {self.name}>"

    
class Product(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        product_name = db.Column(db.String(100), nullable=False)
        current_price = db.Column(db.Float, nullable=False)
        previous_price = db.Column(db.Float)
        in_stock = db.Column(db.Integer)
        product_picture = db.Column(db.String(255), nullable=True)
        flash_sale = db.Column(db.Boolean, default=False)
        date_added = db.Column(db.DateTime, default=datetime.utcnow)
        category_id = db.Column(
            db.Integer,
            db.ForeignKey('category.id', name='fk_category_product'),
            nullable=False,
        ) # ForeignKey to Category

        carts = db.relationship('Cart', backref=db.backref('product', lazy=True))
        orders = db.relationship('Order', backref=db.backref('product', lazy=True))
        
        def __str__(self):
            return '<Product %r>' % self.product_name

    
class Cart(db.Model):
    id= db.Column(db.Integer, primary_key= True)
    quantity= db.Column(db.Integer, nullable= False)
    
    
    customer_link= db.Column(db.Integer, db.ForeignKey('customer.id'), nullable= False)
    product_link= db.Column(db.Integer, db.ForeignKey('product.id'), nullable= False)
    
    def __str__(self):
        return '<Cart %r>' %self.id
    
    
class Order(db.Model):
    id= db.Column(db.Integer, primary_key= True)
    quantity= db.Column(db.Integer, nullable= False)
    price= db.Column(db.Float, nullable=False)
    status= db.Column(db.String(100), nullable= False)
    payment_id= db.Column(db.String(1000), nullable= False)
    
    
    
    customer_link= db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link= db.Column(db.Integer, db.ForeignKey('product.id'), nullable= True)
    
    
    
    def __str__(self):
        return '<Order %r>' %self.id
    



class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return f'<ContactMessage {self.id}>'



class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer, 
        db.ForeignKey('customer.id', ondelete='CASCADE'), 
        nullable=False
    )
    product_id = db.Column(
        db.Integer, 
        db.ForeignKey('product.id', ondelete='CASCADE'), 
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    # relationships (do not use lazy=True here for backref, it's better to define both relationships)
    customer = db.relationship('Customer', backref=db.backref('wishlist_items', cascade='all, delete-orphan', passive_deletes=True))
    product = db.relationship('Product', backref='wishlists')

    def __repr__(self):
        return f'<Wishlist {self.id} - Product {self.product_id}>'



    
    
    
  
