from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Budget, CategoryAllocation, Transaction, Category
from app.budgets import bp
from datetime import datetime

@bp.route('/')
@login_required
def dashboard():
    month = request.args.get('month', None) or datetime.utcnow().strftime('%Y-%m')
    month_date = datetime.strptime(month, '%Y-%m')
    
    budget = Budget.query.filter_by(user_id=current_user.id, month=month_date).first()
    if not budget:
        return render_template('budgets/dashboard.html', budget=None, datetime=datetime)
    
    total_spent = db.session.query(db.func.sum(Transaction.amount))\
        .filter_by(user_id=current_user.id, type='expense')\
        .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
    
    category_allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
    category_spending = {}
    for allocation in category_allocations:
        spent = db.session.query(db.func.sum(Transaction.amount))\
            .filter_by(user_id=current_user.id, category_id=allocation.category_id, type='expense')\
            .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
        category_spending[allocation.category_id] = spent
    
    return render_template('budgets/dashboard.html', 
                           budget=budget, 
                           total_spent=total_spent, 
                           category_spending=category_spending,
                           category_allocations=category_allocations,
                           datetime=datetime)

@bp.route('/list')
@login_required
def list_budgets():
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    if not budgets:
        flash('No budgets defined. Please add a budget.', 'info')
        return render_template('budgets/list.html', budgets=budgets)
    return render_template('budgets/list.html', budgets=budgets)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        month = datetime.strptime(request.form['month'], '%Y-%m')
        total_budget = float(request.form['total_budget'])
        
        # Check for overlapping budgets
        existing_budget = Budget.query.filter_by(user_id=current_user.id, month=month).first()
        if existing_budget:
            flash('A budget for this month already exists.', 'error')
            return redirect(url_for('budgets.list_budgets'))
        
        budget = Budget(
            user_id=current_user.id,
            month=month,
            total_budget=total_budget
        )
        db.session.add(budget)
        db.session.commit()
        
        # Add category allocations
        for allocation in request.form.getlist('category_allocations[][category_id]'):
            category_id = allocation
            percentage = request.form.getlist('category_allocations[][percentage]')[request.form.getlist('category_allocations[][category_id]').index(allocation)]
            allocation = CategoryAllocation(
                budget_id=budget.id,
                category_id=int(category_id),
                percentage=float(percentage)
            )
            db.session.add(allocation)
        
        db.session.commit()
        flash('Budget added successfully', 'success')
        return redirect(url_for('budgets.list_budgets'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/_form.html', categories=categories, budget=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        budget.month = datetime.strptime(request.form['month'], '%Y-%m')
        budget.total_budget = float(request.form['total_budget'])
        
        # Update category allocations
        CategoryAllocation.query.filter_by(budget_id=budget.id).delete()
        for allocation in request.form.getlist('category_allocations[][category_id]'):
            category_id = allocation
            percentage = request.form.getlist('category_allocations[][percentage]')[request.form.getlist('category_allocations[][category_id]').index(allocation)]
            allocation = CategoryAllocation(
                budget_id=budget.id,
                category_id=int(category_id),
                percentage=float(percentage)
            )
            db.session.add(allocation)
        
        db.session.commit()
        flash('Budget updated successfully', 'success')
        return redirect(url_for('budgets.list_budgets'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('budgets/_form.html', budget=budget, categories=categories)

@bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully', 'success')
    return redirect(url_for('budgets.list_budgets'))
