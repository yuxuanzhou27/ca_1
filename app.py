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
@login_required
def index():
    db = get_db()
    user_id = session["user_id"]
    
    # this month
    current_month = datetime.now().strftime("%Y-%m")

    budget_row = db.execute("""SELECT amount 
                                FROM budgets
                                WHERE user_id = ?
                                AND month = ?
                            """, (user_id, current_month)).fetchone()
    if budget_row:
        budget = budget_row["amount"]
    else:
        budget = None

    expense = db.execute("""SELECT SUM(amount) as total
                            FROM transactions
                            WHERE user_id = ?
                            AND type = 'expense'
                            AND strftime('%Y-%m', date) = ?;
                            """, (user_id, current_month)).fetchone()["total"]
    expense = expense if expense else 0
    income = db.execute("""SELECT SUM(amount) as total
                            FROM transactions
                            WHERE user_id = ?
                            AND type = 'income'
                            AND strftime('%Y-%m', date) = ?;
                            """, (user_id, current_month)).fetchone()["total"]
    income = income if income else 0

    if budget:
        remaining = budget - expense
        percent = (expense / budget * 100) if budget else 0
    else:
        remaining = 0
        percent = 0

    return render_template("index.html",
                           budget=budget, expense=expense, income=income, remaining=remaining,
                           percent=round(percent, 2), month=current_month)

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
    user_id = session["user_id"]

    # all transactions
    content = db.execute("""SELECT * FROM transactions
                            WHERE user_id = ?
                            ORDER BY date DESC;
                            """, (user_id,)).fetchall()
    
    # this month
    current_month = datetime.now().strftime("%Y-%m")
    expense = db.execute("""SELECT SUM(amount) as total
                            FROM transactions
                            WHERE user_id = ?
                            AND type = 'expense'
                            AND strftime('%Y-%m', date) = ?;
                            """, (user_id, current_month)).fetchone()["total"]
    income = db.execute("""SELECT SUM(amount) as total
                            FROM transactions
                            WHERE user_id = ?
                            AND type = 'income'
                            AND strftime('%Y-%m', date) = ?;
                            """, (user_id, current_month)).fetchone()["total"]
    expense = expense if expense else 0
    income = income if income else 0

    budget = 1000

    remaining = budget - expense
    percent = (expense / budget * 100) if budget else 0

    return render_template("personal.html", content=content)

@app.route("/set_budget", methods=["POST"])
@login_required
def set_budget():
    db = get_db()
    user_id = session["user_id"]
    current_month = datetime.now().strftime("%Y-%m")

    amount = request.form.get("amount")

    existing = db.execute("""SELECT id FROM budgets
                            WHERE user_id = ?
                            AND month = ?;
                            """, (user_id, current_month)).fetchone()
    if existing:
        db.execute("""UPDATE budgets
                    SET amount = ?
                    WHERE user_id = ?
                    AND month = ?
                    """, (amount, user_id, current_month))
    else:
        db.execute("""INSERT INTO budgets (user_id, month, amount)
                   VALUES (?, ?, ?)
                   """, (user_id, current_month, amount))
    db.commit()

    return redirect(url_for("index"))