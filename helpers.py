import os
from datetime import date, datetime
from calendar import monthrange
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

def budget_categories():
    return ["Food", "Utilities", "Retail/Clothing", "Transport", "Medical", "Recreation/Entertainment", "Others"]


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def remaining_days_to_month_end(date):
    last_day = monthrange(date.year, date.month)[1]
    return last_day - date.day + 1

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year,month)[1])
    return date(year, month, day)

def current_setting(db_settings, target_date):
    for row in reversed(db_settings):
        if row["month_set"] == target_date.strftime("%m-%Y"):
            return row
    return db_settings[-1]

def get_stats(db):
    expenditure_breakdown = {category: 0 for category in budget_categories()}
    cash_in = 0

    #return empty dictionary for months transactions did not take place
    if len(db) < 1:
        return expenditure_breakdown

    for row in db:
        if row["amount"] <=  0:
            expenditure_breakdown[row["category"]] -= row["amount"]
        else:
            cash_in += row["amount"]

    return expenditure_breakdown, cash_in


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def budget_settings_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        db = SQL("sqlite:///budget.db")
        budget_settings = db.execute("SELECT * FROM budget_settings WHERE user_id = ?", session.get("user_id"))
        if len(budget_settings) < 1:
            return redirect("/settings")
        return f(*args, **kwargs)
    return decorated_function

def lookup(symbol):
    """Look up quote for symbol."""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    try: 
        test = float(value)
    except ValueError:
        return value
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${-value:,.2f}"
