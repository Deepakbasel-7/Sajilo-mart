from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = 'database.sqlite3'


def create_database():
    db.create_all()
    print('Database Created')


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'willofD'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    db.init_app(app)
    migrate = Migrate(app, db)

    from .models import Customer, Cart, Wishlist, Product, Order  # Import all needed models

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    # ✅ Global template variables
    @app.context_processor
    def inject_cart_wishlist_counts():
        from flask_login import current_user
        if current_user.is_authenticated:
            cart_count = sum(item.quantity for item in Cart.query.filter_by(customer_link=current_user.id).all())
            wishlist_count = Wishlist.query.filter_by(customer_id=current_user.id).count()
        else:
            cart_count = 0
            wishlist_count = 0
        return dict(cart_count=cart_count, wishlist_count=wishlist_count)

    # Blueprints
    from .views import views
    from .auth import auth
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')

    return app

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'willofD'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    db.init_app(app)

    # Initialize Flask-Migrate with app and db
    migrate = Migrate(app, db)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html')

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(id):
        return Customer.query.get(int(id))

    from .views import views
    from .auth import auth
    from .admin import admin
    from .models import Customer, Cart, Product, Order

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')

    return app
