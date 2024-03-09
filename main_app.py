from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ffjjekejjxnfjidjifjljalksjklfjsk"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db_filename = 'application.db'

# Create tables if they do not exist
def init_db():
    with sqlite3.connect(db_filename) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT, password TEXT NOT NULL)")
        cur.execute("CREATE TABLE IF NOT EXISTS bookings(name TEXT, sir_name TEXT, day_of_booking TEXT, number_of_adults INTEGER, number_of_children INTEGER, age_of_children INTEGER, price INTEGER)")
init_db()
    

class User(UserMixin):
    def __init__(self, id, username, password=None):
        self.id = id
        self.username = username
        self.password = password


@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(db_filename) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        print(f"Loading user with ID: {user_id}")  # Debug print
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()

    if row:
        print(f"Found user row: {row}")  # Debug print
        # Ensure these keys match your database column names
        return User(id=row["id"], username=row["user_name"])
    else:
        print("No user found with that ID.")  # Debug print
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        with sqlite3.connect(db_filename) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_name = ?", (username,))
            user = cur.fetchone()

        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], username=user['user_name'])
            login_user(user_obj)
            if username == "ADMIN":
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('home'))
        else:
            return "Invalid username or password."

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/")
@app.route('/home')
def home():
    if current_user.is_authenticated:
        return render_template("index.html")
    else:
        return render_template("before_login.html")

@app.route("/sign-up", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            hashed_password = generate_password_hash(password)
            
            # Use context manager for database connection
            with sqlite3.connect(db_filename) as conn:
                cur = conn.cursor()
                try:
                    # Insert data into the database
                    cur.execute("INSERT INTO users (user_name, password) VALUES (?, ?)", (username, hashed_password))
                    conn.commit()
                except sqlite3.IntegrityError:
                    return "Username already taken, please choose another"

            return render_template("commferm.html", username=username)
        else:
            return "Invalid user credentials. Go back and try again."

    return render_template("sign_up.html")

@app.route("/about-us")
def about_page():
    return render_template("about.html")

@app.route("/ticketinfo")
def info():
    return render_template("ticketinfo.html")
@app.route("/book", methods=["GET", "POST"])
def book_ticket():
    if request.method == "POST":
        name = request.form.get('fname')
        last_name = request.form.get('lname')
        date = request.form.get('dateofbooking')
        number_of_adults = int(request.form.get("numadults", 0))
        number_of_children = int(request.form.get("numchildren", 0))
        ages_of_children = request.form.getlist("ageofchild")

        # Convert age values to integers and filter out non-digit values
        try:
            ages_of_children = [int(age) for age in ages_of_children if age.isdigit()]
        except ValueError:
            print("Invalid age entry encountered.")
            return "Invalid age data received", 400

        # Calculate price based on adults and children over 5
        adult_price = 6  # Price per adult
        child_price = 3  # Price per child over 5 years old
        price = number_of_adults * adult_price
        for age in ages_of_children:
            if age >= 5:
                price += child_price

        # Insert booking into the database
        with sqlite3.connect(db_filename) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO bookings (name, sir_name, day_of_booking, number_of_adults, number_of_children, age_of_children, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, last_name, date, number_of_adults, number_of_children, ','.join(map(str, ages_of_children)), price))
            conn.commit()

        return render_template("booked.html", name=name, last_name=last_name, date=date, price=price)
    return render_template("booking.html")

@app.route("/admin")
def admin():
    return "admin"
        
    
    
if __name__ == '__main__':
    app.run(debug=True)
