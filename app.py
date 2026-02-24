from flask import Flask, render_template, redirect, session, url_for, g, request
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegistrationForm, TransactionForm
from functools import wraps
from datetime import datetime

app=Flask(__name__)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.teardown_appcontext(close_db)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():

        user_id = form.user_id.data
        password = form.password.data
        password2 = form.password2.data

        db = get_db()
        conflict = db.execute("""SELECT * FROM users
                            WHERE user_id = ?;
                            """, (user_id,)).fetchone()
        if conflict is not None:
            form.user_id.errors.append("User id conflicts with another")
        else:
            db.execute("""INSERT INTO users (user_id, password)
                            VALUES (?, ?);
                           """, (user_id, generate_password_hash(password)))
            db.commit()
            return redirect(url_for("login"))
        
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user_id = form.user_id.data
        password = form.password.data

        db = get_db()
        matching_user = db.execute("""SELECT * FROM users
                            WHERE user_id = ?;
                            """, (user_id,)).fetchone()
        if matching_user is None:
            form.user_id.errors.append("Unknown user id")
        elif not check_password_hash(matching_user["password"], password):
            form.password.errors.append("Incorrect password")
        else:
            session.clear()
            session["user_id"] = user_id
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
        
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/add_transactions", methods=["GET", "POST"])
@login_required
def add_transactions():
    form = TransactionForm()
    if form.validate_on_submit():
        currency = form.currency.data
        amount = form.amount.data
        type = form.type.data
        category = form.category.data
        db = get_db()
        db.execute("""INSERT INTO transactions (user_id, currency, amount, type, category, date)
                         VALUES (?, ?, ?, ?, ?, ?)
                      """,(session["user_id"], currency, amount, type, category, datetime.now().date()))
        db.commit()
    return render_template("add_transactions.html", form=form)

@app.route("/personal")
@login_required
def personal():
    db = get_db()
    content = db.execute("""SELECT * FROM transactions
                            WHERE user_id = ?;
                            """, (session["user_id"],)).fetchall()
    return render_template("personal.html", content=content)