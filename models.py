from flask_sqlalchemy import SQLAlchemy

# Initialize database instance
db = SQLAlchemy()

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='buyer')

    products = db.relationship('Product', backref='seller', foreign_keys='Product.seller_id', lazy=True)
    purchases = db.relationship('Product', backref='buyer', foreign_keys='Product.buyer_id', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# Product model
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_sold = db.Column(db.Boolean, default=False)

    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'<Product {self.title}>'
