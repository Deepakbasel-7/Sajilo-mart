from website import db, create_app
from .models import Product, Category

app = create_app()
with app.app_context():
    categories = [
        "Supermarket", "Health & Beauty", "Home & Office", "Fashion",
        "Electronics", "Gaming", "Baby Products", "Sporting Goods", "Garden & Outdoor"
    ]
    for category_name in categories:
        category = Category(name=category_name)
        db.session.add(category)
    db.session.commit()
    print("Categories added successfully.")
