from flask import render_template, redirect, url_for
from flask_login import current_user
from app.main import bp
from app.models import Transaction, Category, Budget, CategoryAllocation
from app import db
from app.auth.forms import LoginForm
from app.budgets import bp as budgets_bp
from datetime import datetime

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        transactions = Transaction.query.filter_by(user_id=current_user.id)\
            .order_by(Transaction.date.desc()).limit(5).all()
        
        # Calculate total income and expenses
        income = db.session.query(db.func.sum(Transaction.amount))\
            .filter_by(user_id=current_user.id, type='income').scalar() or 0
        expenses = db.session.query(db.func.sum(Transaction.amount))\
            .filter_by(user_id=current_user.id, type='expense').scalar() or 0
        
        # Calculate category allocations and spending
        month = datetime.utcnow().strftime('%Y-%m')
        month_date = datetime.strptime(month, '%Y-%m')
        budget = Budget.query.filter_by(user_id=current_user.id, month=month_date).first()
        category_allocations = []
        category_spending = {}
        if budget:
            category_allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
            for allocation in category_allocations:
                spent = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(user_id=current_user.id, category_id=allocation.category_id, type='expense')\
                    .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
                category_spending[allocation.category_id] = spent
        
        return render_template('index.html',
                             transactions=transactions,
                             total_income=income,
                             total_expenses=expenses,
                             balance=income - expenses,
                             category_allocations=category_allocations,
                             category_spending=category_spending)
    
    # Show landing page with login form for unauthenticated users
    form = LoginForm()
    return render_template('landing.html', form=form)
