from flask import Flask, render_template, redirect, session, url_for, g, request
from database import get_db, close_db
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegistrationForm, TransactionForm
from functools import wraps
from datetime import datetime

EXCHANGE_RATE = {
    ("EUR", "CNY") : 8.0,
    ("CNY", "EUR") : 1 / 8.0
}

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

    budget_row = db.execute("""SELECT amount, currency
                                FROM budgets
                                WHERE user_id = ?
                                AND month = ?
                            """, (user_id, current_month)).fetchone()
    if budget_row:
        budget = convert(budget_row["amount"], budget_row["currency"], "EUR")
    else:
        budget = None

    rows = db.execute("""SELECT amount, currency 
                        FROM transactions
                        WHERE user_id = ?
                        AND type = 'expense'
                        AND strftime('%Y-%m', date) = ?
                     """, (user_id, current_month)).fetchall()
    expense = 0
    for row in rows:
        expense += convert(row["amount"], row["currency"], "EUR")
    expense = round(expense, 2)
    
    rows = db.execute("""SELECT amount, currency 
                        FROM transactions
                        WHERE user_id = ?
                        AND type = 'income'
                        AND strftime('%Y-%m', date) = ?
                     """, (user_id, current_month)).fetchall()
    income = 0
    for row in rows:
        income += convert(row["amount"], row["currency"], "EUR")
    income = round(income, 2)

    if budget:
        remaining = budget - expense
        percent = (expense / budget * 100) if budget else 0
    else:
        remaining = 0
        percent = 0

    quicks = db.execute("""SELECT * FROM quick
                           WHERE user_id = ?
                           """, (user_id,)).fetchall()

    return render_template("index.html",
                           budget=budget, expense=expense, income=income, remaining=remaining,
                           percent=round(percent, 2), month=current_month, 
                           quicks=quicks)

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
            return redirect(url_for("login", user_id=form.user_id.data))
        
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    user_id = request.args.get("user_id")

    if request.method == "GET" and user_id:
        form.user_id.data = user_id

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
    db = get_db()

    if form.validate_on_submit():
        currency = form.currency.data
        amount = form.amount.data
        type = form.type.data
        category = form.category.data
        description = form.description.data
        
        db.execute("""INSERT INTO transactions (user_id, currency, amount, type, category, date, description)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                      """,(session["user_id"], currency, amount, type, category, datetime.now().date(), description))
        db.commit()
        return redirect(url_for("add_transactions"))
    
    return render_template("add_transactions.html", form=form)

@app.route("/personal")
@login_required
def personal():
    db = get_db()
    user_id = session["user_id"]

    # all transactions
    query = request.args.get("q")
    category = request.args.get("category")

    if query and category:
        content = db.execute("""SELECT * FROM transactions
                            WHERE user_id = ?
                            AND description LIKE ?
                            AND category = ?
                            ORDER BY date DESC
                            """, (user_id, f"%{query}%", category)).fetchall()
    elif query:
        content = db.execute("""SELECT * FROM transactions
                            WHERE user_id = ?
                            AND description LIKE ?
                            ORDER BY date DESC
                            """, (user_id, f"%{query}%")).fetchall()
    elif category:
        content = db.execute("""SELECT *
                        FROM transactions
                        WHERE user_id = ?
                        AND category = ?
                        ORDER BY date DESC
                     """, (user_id, category)).fetchall()
    else:
        content = db.execute("""SELECT * FROM transactions
                            WHERE user_id = ?
                            ORDER BY date DESC
                            """, (user_id,)).fetchall()
        
    categories = db.execute("""SELECT DISTINCT category
                            FROM transactions
                            WHERE user_id = ?
                            ORDER BY category
                            """, (user_id,)).fetchall()
    
    # this month
    current_month = datetime.now().strftime("%Y-%m")

    rows = db.execute("""SELECT amount, currency 
                        FROM transactions
                        WHERE user_id = ?
                        AND type = 'expense'
                        AND strftime('%Y-%m', date) = ?
                     """, (user_id, current_month)).fetchall()
    expense = 0
    for row in rows:
        expense += convert(row["amount"], row["currency"], "EUR")
    expense = round(expense, 2)

    rows = db.execute("""SELECT amount, currency 
                        FROM transactions
                        WHERE user_id = ?
                        AND type = 'income'
                        AND strftime('%Y-%m', date) = ?
                     """, (user_id, current_month)).fetchall()
    income = 0
    for row in rows:
        income += convert(row["amount"], row["currency"], "EUR")
    income = round(income, 2)
    
    expense = expense if expense else 0
    income = income if income else 0

    budget = 1000

    remaining = budget - expense
    percent = (expense / budget * 100) if budget else 0

    

    return render_template("personal.html", content=content, categories=categories)

@app.route("/set_budget", methods=["POST"])
@login_required
def set_budget():
    db = get_db()
    user_id = session["user_id"]
    current_month = datetime.now().strftime("%Y-%m")

    amount = request.form.get("amount")
    currency = request.form.get("currency")

    existing = db.execute("""SELECT id FROM budgets
                            WHERE user_id = ?
                            AND month = ?
                            """, (user_id, current_month)).fetchone()
    if existing:
        db.execute("""UPDATE budgets
                    SET amount = ?
                    WHERE user_id = ?
                    AND month = ?
                    AND currency = ?
                    """, (amount, user_id, current_month, currency))
    else:
        db.execute("""INSERT INTO budgets (user_id, month, currency, amount)
                   VALUES (?, ?, ?, ?)
                   """, (user_id, current_month, currency, amount))
    db.commit()

    return redirect(url_for("index"))

# create a new button for quick adding
@app.route("/add_template", methods=["POST"])
@login_required
def add_template():
    user_id = session["user_id"]

    currency = request.form.get("currency")
    amount = request.form.get("amount")
    type = request.form.get("type")
    category = request.form.get("category")
    
    db = get_db()
    db.execute("""INSERT INTO quick (user_id, currency, amount, type, category)
                VALUES (?, ?, ?, ?, ?)
               """, (user_id, currency, amount, type, category))
    db.commit()

    return redirect("/")

# if you click this button, you can get a new trasaction
@app.route("/quick_add/<int:template_id>", methods=["POST"])
@login_required
def quick_add(template_id):
    user_id= session["user_id"]
    db = get_db()
    template = db.execute("""SELECT * FROM quick
                          WHERE id = ?
                          AND user_id = ?
                          """, (template_id, user_id)).fetchall()
    if not template:
        return redirect("/")
    
    template = template[0]
    
    db.execute("""INSERT INTO transactions (user_id, currency, amount, type, category, date)
               VALUES(?, ?, ?, ?, ?, DATE('now'), ?)
               """, (user_id, template["currency"], template["amount"], template["type"], template["category"], "quick add"))
    db.commit()

    return redirect("/")

def convert(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return amount
    rate = EXCHANGE_RATE[(from_currency, to_currency)]
    return amount * rate