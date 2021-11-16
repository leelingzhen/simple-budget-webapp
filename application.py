import os
import sys
from datetime import datetime, date, timedelta

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import *

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///budget.db")


@app.route("/change_password", methods=["GET","POST"])
@login_required
def change_password(): ####
    if request.method =="POST":

        #ensure fields are not left blank
        if (not request.form.get("current_password") or (not request.form.get("new_password")) or (not request.form.get("confirmation_password"))):
            flash("Settings are unchanged")
            return redirect("/")
        
        user = db.execute("SELECT hash FROM users WHERE id=?", session.get("user_id"))
        #ensure password is correct
        if not check_password_hash(user[0]["hash"], request.form.get("current_password")):
            flash("Password is incorrect")
            return redirect("/change_password") 

        #ensure user enters a new password that is different from the current password
        if check_password_hash(user[0]["hash"], request.form.get("new_password")):
            flash("Password entered is the same please use a new password")
            return redirect("/change_password") 

        #ensure passwords match
        if request.form.get("new_password") != request.form.get("confirmation_password"):
            flash("Passwords do not match")
            return redirect("/change_password")

        db.execute("BEGIN TRANSACTION")
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(request.form.get("new_password")), session.get("user_id"))
        db.execute("COMMIT")
        flash("Password has been changed")
        return redirect("/")
    
    else:
        return render_template("change_password.html")


@app.route("/", methods=["GET", "POST"])
@login_required
@budget_settings_required
def index():
    """Show today's expenditure and daily budget balance""" 
    if request.method == "GET":
        budget_date = datetime.today()
    else:
        if request.form.get("date") != '':
            budget_date = request.form.get("date")
            budget_date = datetime.strptime(budget_date, "%Y-%m-%d")
        else:
            budget_date = datetime.today()

    day_entries = db.execute("SELECT * FROM transactions WHERE timestamp LIKE ? AND user_id = ?", budget_date.strftime("%d-%m-%Y")+"%", session.get("user_id"))
    month_entries = db.execute("SELECT * FROM transactions WHERE timestamp LIKE ? AND user_id = ?", f'%{budget_date.strftime("%m-%Y")}%', session.get("user_id"))
    remaining_days = remaining_days_to_month_end(budget_date)

    budget_settings = db.execute("SELECT * FROM budget_settings WHERE user_id = ?", session.get("user_id"))
    month_budget_balance = current_setting(budget_settings, budget_date)["monthly_budget"]
    day_budget_balance = month_budget_balance
    for row in month_entries:
        row_date = datetime.strptime(row["timestamp"], "%d-%m-%Y, %H:%M:%S")
        if row_date < budget_date:
           day_budget_balance += row["amount"]
        month_budget_balance += row["amount"]
    day_budget_balance /= remaining_days
    for row in day_entries:
        day_budget_balance += row["amount"]
    display_date = budget_date.strftime("%Y-%m-%d")
    return render_template("homepage.html", display_date=display_date, day_entries=day_entries, day_budget_balance=day_budget_balance, month_budget_balance=month_budget_balance)

@app.route("/edit_entry", methods=["GET", "POST"])
@login_required
@budget_settings_required
def edit_entry():
    
    if request.method == "POST":
        categories = budget_categories()
        entry = db.execute("SELECT * FROM transactions WHERE id = ?", request.form.get("id"))[0]
        if request.form.get("delete") == "true":
            db.execute("BEGIN TRANSACTION")
            db.execute("DELETE FROM transactions WHERE id = ?", request.form.get("id"))
            db.execute("COMMIT")
            flash("Entry has been deleted")
            return redirect("/")

        if not request.form.get("category") or not request.form.get("amount"):
            flash("Changes Discarded")
            return redirect("/")
        if request.form.get("category") not in categories:
            flash("Invalid category, use the remarks field instead")
            return redirect("/")
        category = request.form.get("category")
        amount = - float(request.form.get("amount"))
        if request.form.get("datetime") == "":
            input_date = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
        else:
            input_date = datetime.strptime(request.form.get("datetime"), "%Y-%m-%dT%H:%M").strftime("%d-%m-%Y, %H:%M:%S")
        if request.form.get("add_cash") == "yes":
            amount = - amount

        db.execute("BEGIN TRANSACTION")
        db.execute("UPDATE transactions SET timestamp = ?, category = ?, amount = ?, remarks = ? WHERE id = ?", input_date, category, amount, request.form.get("remarks"), request.form.get("id"))
        db.execute("COMMIT")
        flash("Entry has been updated")
        return redirect("/")
    else:
        if not request.args.get("edit"):
            flash("No entries selected")
            return redirect("/")
        categories = ["Food", "Utilities", "Retail/Clothing", "Transport", "Medical", "Recreation/Entertainment", "Others"]
        entry = db.execute("SELECT * FROM transactions WHERE id = ?", request.args.get("edit"))[0]
        return render_template("edit_entry.html",id=request.args.get("edit"), categories=categories, entry=entry, timestamp=datetime.strptime(entry["timestamp"], "%d-%m-%Y, %H:%M:%S").strftime("%Y-%m-%dT%H:%M"))



@app.route("/add_entry", methods=["GET", "POST"])
@login_required
@budget_settings_required
def add_entry():
    categories = budget_categories()
    if request.method == "POST":
        if not request.form.get("category") or not request.form.get("amount"):
            flash("No entries added")
            return redirect("/")
        if request.form.get("category") not in categories:
            flash("Invalid category, use the remarks field instead")
            return render_template("/add_entry.html", categories=categories, datetime_now=datetime.now().strftime("%Y-%m-%dT%H:%M"))
        category = request.form.get("category")
        amount = - float(request.form.get("amount"))
        if request.form.get("datetime") == "" or request.form.get("datetime") == datetime.now().strftime("%Y-%m-%dT%H:%M"):
            input_date = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
        else:
            input_date = datetime.strptime(request.form.get("datetime"), "%Y-%m-%dT%H:%M").strftime("%d-%m-%Y, %H:%M:%S")
        if request.form.get("add_cash") == "yes":
            amount = - amount

        db.execute("BEGIN TRANSACTION")
        db.execute("INSERT INTO transactions (timestamp, user_id, category, amount, remarks) VALUES (?,?,?,?,?)", input_date, session.get("user_id"), category, amount, request.form.get("remarks"))
        db.execute("COMMIT")
        flash("Entry has been added")
        return redirect("/")
    else:
        return render_template("/add_entry.html", categories=categories, datetime_now=datetime.now().strftime("%Y-%m-%dT%H:%M"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Username cannot be left blank")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password cannot be left blank")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash(f"Welcome back, {request.form.get('username')}.\n")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user""" 
    if request.method == "POST":
        #render redirect if username is blank
        if not request.form.get("username"):
            flash("Username cannot be left blank")
            return redirect("/register")
        
        #render redirect if either password fields are blank
        if not (request.form.get("password")) or (not request.form.get("confirmation")):
            flash("Passwords cannot be left blank")
            return redirect("/register")

        #render redirect if username has already been taken
        username = request.form.get("username")
        existing_users = db.execute("SELECT username FROM users WHERE username = ?", username)
        if len(existing_users) > 0: 
            flash("Username has already been taken")
            return redirect("/register")


        #render redirect if passwords do not match
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            flash("Passwords do not match")
            return redirect("/register")

        db.execute("BEGIN TRANSACTION")
        #store hashed password in db
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, generate_password_hash(password, method='pbkdf2:sha256'))
        db.execute("COMMIT")
        #get user_id from db
        user_record = db.execute("SELECT * FROM users WHERE username=?", username)
        session["user_id"] = user_record[0]["id"]
        flash(f'Welcome, {username}.\n')
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    budget_settings = db.execute("SELECT * FROM budget_settings WHERE user_id = ?", session.get("user_id"))

    if request.method == "POST":
        if len(budget_settings) < 1 and (not request.form.get("monthly_income") or not request.form.get("monthly_expenditure") or not request.form.get("monthly_savings")):
            flash("Budget has not been set up, fields cannot be left blank")
            return redirect("/settings")
        if not request.form.get("monthly_income") and not request.form.get("monthly_expenditure") and not request.form.get("monthly_savings"):
            flash("Budget settings left unchanged")
            return redirect("/")
        #retrieve settings from form
        try:
            income = float(request.form.get("monthly_income"))
            expenditure = float(request.form.get("monthly_expenditure"))
            savings = float(request.form.get("monthly_savings"))
        except ValueError:
            flash("Fields only accept numeric inputs")
            return redirect("/settings")
        if request.form.get("month_select") == "This Month":
            month_select = datetime.now().strftime("%m-%Y")
        elif request.form.get("month_select") == "Next Month":
            month_select = add_months(datetime.now(), 1).strftime("%m-%Y")
        else:
            flash("Invalid Selection")
            return redirect ("/settings")

        db.execute("BEGIN TRANSACTION")
        #if budget_settings have not been setup yet
        if len(budget_settings) < 1:
            flash_message = "Your budget setup has been sucessful"
        else:
            flash_message = "Budget settings have been updated."
            
        db.execute("INSERT INTO budget_settings (month_set, user_id, monthly_income, fixed_expenditure, fixed_savings, monthly_budget ) VALUES (?,?,?,?,?,?)",
                    month_select, session.get("user_id"), income, expenditure, savings, income - expenditure - savings
                    )
        db.execute("COMMIT")

        flash(flash_message)
        return redirect("/")

    else:
        if len(budget_settings) < 1:
            flash("\nYour budget has not been set up yet, please set it up before proceeding")
            return render_template("settings.html", income=0, expenditure=0, savings=0, budget=0)
        else:
            select_settings = current_setting(budget_settings, datetime.now())  
            return render_template("settings.html", income=select_settings["monthly_income"], expenditure=select_settings["fixed_expenditure"], savings=select_settings["fixed_savings"], budget=select_settings["monthly_budget"])

@app.route("/monthly_summary", methods=["GET","POST"])
@login_required
@budget_settings_required
def monthly_summary():
    if request.method =="POST":
        selected_month = datetime.strptime(request.form.get("month"), "%Y-%m")
    else:
        selected_month = date.today()

    month_transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? AND timestamp LIKE ?", session.get("user_id"), f'%{selected_month.strftime("%m-%Y")}%')
    month_budget_settings = current_setting(db.execute("SELECT * FROM budget_settings WHERE user_id = ?", session.get("user_id")), selected_month)
    stats, cash_in = get_stats(month_transactions)
    total_expenses = sum([expense for category, expense in stats.items()])
    month_budget_balance = month_budget_settings["monthly_budget"] - total_expenses + cash_in
    table_output = [
            ["Budget plan last set", datetime.strptime(month_budget_settings["month_set"], "%m-%Y").strftime("%B %Y")],
            ["Income", month_budget_settings['monthly_income']],
            ["Fixed Expenses", month_budget_settings["fixed_expenditure"]],
            ["Target Savings", month_budget_settings["fixed_savings"]],
            ["Monthly Budget", month_budget_settings["monthly_budget"]],
            ['',''],
            ["Total Expenses", total_expenses],
            ["Cash Inflow", cash_in],
            ["Month Budget Balance", month_budget_balance],
            ["Actual Savings", month_budget_settings["fixed_savings"] + month_budget_balance]
            ]

    return render_template("monthly_summary.html",month_input=selected_month.strftime("%Y-%m"), stats=stats , table_output=table_output)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
