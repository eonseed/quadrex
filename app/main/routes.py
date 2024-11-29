from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.models import Transaction, Category
from app import db

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.date.desc()).limit(5).all()
    
    # Calculate total income and expenses
    income = db.session.query(db.func.sum(Transaction.amount))\
        .filter_by(user_id=current_user.id, type='income').scalar() or 0
    expenses = db.session.query(db.func.sum(Transaction.amount))\
        .filter_by(user_id=current_user.id, type='expense').scalar() or 0
    
    return render_template('index.html',
                         transactions=transactions,
                         total_income=income,
                         total_expenses=expenses,
                         balance=income - expenses)
