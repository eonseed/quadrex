from flask import render_template, redirect, url_for, current_app
from flask_login import current_user
from app.main import bp
from app.models import Transaction, Category, Budget, CategoryAllocation
from app import db
from app.auth.forms import LoginForm
from app.budgets import bp as budgets_bp
from datetime import datetime
import logging

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
        current_time = datetime.now()
        month_date = datetime(current_time.year, current_time.month, 1).date()  # First day of current month
        
        current_app.logger.info(f"Looking for budget with user_id={current_user.id} and month={month_date}")
        
        # Get budget for the month
        budget = Budget.query.filter_by(
            user_id=current_user.id,
            month=month_date
        ).first()
        
        # If no budget exists for current month, try to find the most recent budget
        if not budget:
            budget = Budget.query.filter_by(user_id=current_user.id)\
                .order_by(Budget.month.desc()).first()
            if budget:
                month_date = budget.month
                current_app.logger.info(f"No budget for current month, using most recent: {month_date}")
        
        current_app.logger.info(f"Found budget: {budget}")
        if budget:
            current_app.logger.info(f"Budget total: {budget.total_budget}")
        
        total_budget = 0
        total_spent = 0
        category_allocations = []
        category_spending = {}
        
        if budget:
            total_budget = budget.total_budget
            
            # Calculate total spent for the month
            month_start = month_date
            month_end = datetime(month_date.year, month_date.month + 1, 1).date() if month_date.month < 12 \
                else datetime(month_date.year + 1, 1, 1).date()
            
            current_app.logger.info(f"Calculating spending between {month_start} and {month_end}")
            
            total_spent = db.session.query(db.func.sum(Transaction.amount))\
                .filter_by(user_id=current_user.id, type='expense')\
                .filter(Transaction.date >= month_start)\
                .filter(Transaction.date < month_end)\
                .scalar() or 0
            
            current_app.logger.info(f"Total spent: {total_spent}")
            
            # Get allocated categories spending
            category_allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
            allocated_categories = [alloc.category_id for alloc in category_allocations]
            
            current_app.logger.info(f"Found {len(category_allocations)} category allocations")
            
            # Calculate spending for allocated categories
            for allocation in category_allocations:
                spent = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(user_id=current_user.id, category_id=allocation.category_id, type='expense')\
                    .filter(Transaction.date >= month_start)\
                    .filter(Transaction.date < month_end)\
                    .scalar() or 0
                category_spending[allocation.category_id] = spent
                current_app.logger.info(f"Category {allocation.category_id} spent: {spent}")
            
            # Calculate spending for unallocated categories as "Others"
            if allocated_categories:  # Only calculate others if there are allocated categories
                others_spent = db.session.query(db.func.sum(Transaction.amount))\
                    .filter_by(user_id=current_user.id, type='expense')\
                    .filter(Transaction.date >= month_start)\
                    .filter(Transaction.date < month_end)\
                    .filter(~Transaction.category_id.in_(allocated_categories))\
                    .scalar() or 0
                
                if others_spent > 0:
                    category_spending['others'] = others_spent
                    current_app.logger.info(f"Others category spent: {others_spent}")
        
        # Log final values being passed to template
        current_app.logger.info(f"Rendering template with: budget={total_budget}, spent={total_spent}")
        
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

@bp.route('/debug_budget')
def debug_budget():
    if not current_user.is_authenticated:
        return "Not authenticated"
    
    current_time = datetime.strptime('2024-12-07T16:58:53+08:00', '%Y-%m-%dT%H:%M:%S%z')
    month_date = datetime(current_time.year, current_time.month, 1).date()
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    
    debug_info = []
    debug_info.append(f"Looking for budget on {month_date}")
    debug_info.append(f"Found {len(budgets)} budgets for user {current_user.id}")
    
    for budget in budgets:
        debug_info.append(f"Budget: month={budget.month}, total={budget.total_budget}")
        allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
        debug_info.append(f"  Allocations: {len(allocations)}")
        for alloc in allocations:
            category = Category.query.get(alloc.category_id)
            debug_info.append(f"    - {category.name}: {alloc.percentage}%")
    
    return "<br>".join(debug_info)
