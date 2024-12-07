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
        
        # Calculate category allocations and spending for current month
        month = datetime.utcnow().strftime('%Y-%m')
        if datetime.utcnow() > datetime(2024, 12, 1):
            month = '2024-12'  # Force December for testing
        month_date = datetime.strptime(month, '%Y-%m')
        
        # Get budget for the month
        budget = Budget.query.filter_by(user_id=current_user.id, month=month_date).first()
        total_budget = 0
        total_spent = 0
        category_allocations = []
        category_spending = {}
        
        if budget:
            total_budget = budget.total_budget
            # Calculate total spent for the month
            total_spent = db.session.query(db.func.sum(Transaction.amount))\
                .filter_by(user_id=current_user.id, type='expense')\
                .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
            
            # Get allocated categories spending
            category_allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
            allocated_categories = [alloc.category_id for alloc in category_allocations]
            
            # Calculate spending for allocated categories
            for allocation in category_allocations:
                spent = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(user_id=current_user.id, category_id=allocation.category_id, type='expense')\
                    .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
                category_spending[allocation.category_id] = spent
            
            # Calculate spending for unallocated categories as "Others"
            if allocated_categories:  # Only calculate others if there are allocated categories
                others_spent = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(user_id=current_user.id, type='expense')\
                    .filter(db.func.strftime('%Y-%m', Transaction.date) == month)\
                    .filter(~Transaction.category_id.in_(allocated_categories)).scalar() or 0
                
                if others_spent > 0:
                    category_spending['others'] = others_spent
        
        return render_template('index.html',
                             transactions=transactions,
                             total_income=income,
                             total_expenses=expenses,
                             balance=income - expenses,
                             total_budget=total_budget,
                             total_spent=total_spent,
                             category_allocations=category_allocations,
                             category_spending=category_spending,
                             current_month=month_date)
    
    # Show landing page with login form for unauthenticated users
    form = LoginForm()
    return render_template('landing.html', form=form)
