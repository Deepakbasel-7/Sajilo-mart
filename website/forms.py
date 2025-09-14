from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, length, NumberRange
from wtforms.validators import DataRequired, Email, Length

from .models import Category


class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), length(min=2)])
    password1 = PasswordField('Enter your Password', validators=[DataRequired(), length(min=6)])
    password2 = PasswordField('Confirm your Password', validators=[DataRequired(), length(min=6)])
    submit = SubmitField('Sign up')
    


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), length(min=3)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")
    
    
class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators= [DataRequired(), length(min=6)])
    new_password = PasswordField('New Password', validators= [DataRequired(), length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators= [DataRequired(), length(min=6)])
    change_password= SubmitField('Change Password')
    
    
    
class ShopItemsForm(FlaskForm):
    product_name = StringField('Name of Product', validators=[DataRequired()])
    current_price = FloatField('Current Price', validators=[DataRequired()])
    previous_price = FloatField('Previous Price', validators=[DataRequired()])
    in_stock = IntegerField('In Stock', validators=[DataRequired(), NumberRange(min=0)])
    # product_picture = FileField('Product Picture')  # Made optional for updates
    flash_sale = BooleanField('Flash Sale')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])

    add_product = SubmitField('Add Product')
    update_product = SubmitField('Update')

    def __init__(self, *args, **kwargs):
        super(ShopItemsForm, self).__init__(*args, **kwargs)
        # Dynamically populate the categories
        self.category_id.choices = [(category.id, category.name) for category in Category.query.all()]



    
    
class OrderForm(FlaskForm):
    order_status= SelectField('Order Status', choices=[('Pending','Pending'),('Accepted','Accepted'),
                                                       ('Out for delivery','Out for delivery'),('Delivered','Delivered'),
                                                       ('Canceled','Canceled')])
    
    update= SubmitField('Update Status')







