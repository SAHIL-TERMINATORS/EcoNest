from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from collections import Counter
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv() 
# ------------------ Initialize Flask App ------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)



# ------------------ Configuration ------------------
MYSQL_USER = 'root'
MYSQL_PASSWORD = '29042004'
MYSQL_DB = 'student'
MYSQL_HOST = 'localhost'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_PERMANENT'] = False

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ------------------ Database Setup ------------------
db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db
Session(app)

# ------------------ Models ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    projects = db.relationship('Project', backref='owner', lazy=True)
    uploads = db.relationship('Upload', backref='uploader', lazy=True)
    uploaded_products = db.relationship('Product', foreign_keys='Product.uploaded_by', backref='uploader', lazy=True)
    purchased_products = db.relationship('Product', foreign_keys='Product.buyer_id', backref='buyer', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

from datetime import datetime

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_sold = db.Column(db.Boolean, default=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ IMPORTANT
    sold = db.Column(db.Boolean, default=False)


    @property
    def timestamp(self):
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")

    



class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ Utility Functions ------------------

CORS(app)  # Enable CORS if needed

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')  # Your email
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Your email password or app password
RECIPIENT_EMAIL = 'sahiljouhari2004@gmail.com'  # Recipient email

@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        data = request.json
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"New Contact Form Submission: {data['subject']}"
        
        body = f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {data['name']}</p>
        <p><strong>Email:</strong> {data['email']}</p>
        <p><strong>Subject:</strong> {data['subject']}</p>
        <p><strong>Message:</strong></p>
        <p>{data['message']}</p>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return jsonify({'message': 'Your message has been sent successfully!'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_user(username):
    return User.query.filter_by(username=username).first()

# ------------------ Routes ------------------
@app.route("/")
def home():
    projects = Project.query.all()
    return render_template("index.html", projects=projects)

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("profile"))
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        role = request.form.get("role", "user")
        
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))
        if get_user(username):
            flash("Username already exists.", "danger")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw, role=role)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        role = session.get("role")
        return redirect(url_for(f"{role}_dashboard"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = get_user(username)

        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Login successful", "success")
            return redirect(url_for(f"{user.role}_dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    user = get_user(session["user"])
    purchases = Product.query.filter_by(buyer_id=user.id).all()
    return render_template("profile.html", user=user, projects=user.projects, uploads=user.uploads, purchases=purchases)




from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])

        if 'image' not in request.files or request.files['image'].filename == '':
            flash("No image uploaded!", "danger")
            return redirect(request.url)

        image = request.files['image']
        filename = secure_filename(image.filename)
        image_path = os.path.join('static/uploads', filename)
        image.save(image_path)

        # ✅ Get the currently logged-in user's ID
        uploaded_by = session.get('user_id')  # or current_user.id if using Flask-Login

        if not uploaded_by:
            flash("Please login first!", "warning")
            return redirect(url_for('login'))

        new_product = Product(
            title=title,
            description=description,
            price=price,
            image_path=f"uploads/{filename}",
            uploaded_by=uploaded_by,   # ✅ Fix applied here
            is_sold=False,
            buyer_id=None,
            created_at=datetime.utcnow()
        )

        db.session.add(new_product)
        db.session.commit()

        flash("Product uploaded successfully!", "success")
        return redirect(url_for('seller_dashboard'))

    return render_template("upload.html")




@app.route('/user_dashboard')
def user_dashboard():
    products = Product.query.filter_by(sold=False).all()
    return render_template('user_dashboard.html', products=products)

@app.route("/seller_dashboard")
def seller_dashboard():
    if session.get("role") != "seller":
        return redirect(url_for("login"))

    products = Product.query.filter_by(uploaded_by=session["user_id"]).all()

    sold_products = [p for p in products if p.is_sold]
    earnings = sum(p.price for p in sold_products)

    return render_template("seller_dashboard.html", 
                           products=products,
                           total_products=len(products),
                           sold_products=len(sold_products),
                           total_earnings=earnings)



@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    users = User.query.all()
    products = Product.query.all()
    role_counts = Counter([user.role for user in users])
    monthly_uploads = [0]*12
    for product in products:
        if product.created_at:
            monthly_uploads[product.created_at.month - 1] += 1
    return render_template("admin_dashboard.html", 
                           users=users, 
                           products=products,
                           role_counts=role_counts,
                           monthly_uploads=monthly_uploads)

@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if session.get("user_id") != product.uploaded_by and session.get("role") != "admin":
        flash("Unauthorized.", "danger")
        return redirect(url_for("home"))
    if request.method == "POST":
        product.title = request.form["title"]
        product.price = float(request.form["price"])
        product.is_sold = request.form.get("is_sold") == "true"
        db.session.commit()
        flash("Product updated!", "success")
        return redirect(url_for("seller_dashboard"))
    return render_template("edit_product.html", product=product)

@app.route("/delete_product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("seller_dashboard"))

@app.route("/mark_as_sold/<int:product_id>", methods=["POST"])
def mark_as_sold(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_sold = True
    product.buyer_id = session.get("user_id")
    db.session.commit()
    flash("Marked as sold.", "success")
    return redirect(url_for("seller_dashboard"))

@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    user = User.query.get_or_404(user_id)
    Product.query.filter_by(uploaded_by=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "info")
    return redirect(url_for("admin_dashboard"))

@app.route("/change_role/<int:user_id>", methods=["POST"])
def change_role(user_id):
    if session.get("role") != "admin":
        flash("Unauthorized", "danger")
        return redirect(url_for("home"))
    user = User.query.get_or_404(user_id)
    role = request.form.get("new_role")
    if role in ["user", "seller", "admin"]:
        user.role = role
        db.session.commit()
        flash("Role changed.", "success")
    else:
        flash("Invalid role.", "danger")
    return redirect(url_for("admin_dashboard"))

# ------------------ Static Pages ------------------
@app.route("/news")
def news(): return render_template("news.html")

@app.route("/stories")
def stories(): return render_template("stories.html")

@app.route("/events")
def events(): return render_template("events.html")

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/contact")
def contact(): return render_template("contact.html")

@app.route("/resources")
def resources(): return render_template("resources.html")

# ------------------ Run App ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
