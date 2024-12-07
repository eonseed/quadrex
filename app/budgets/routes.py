from flask import render_template, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Budget, CategoryAllocation, Transaction, Category
from app.budgets import bp
from datetime import datetime

@bp.route('/')
@login_required
def dashboard():
    # Get the current month if not specified, defaulting to December 2024
    default_month = '2024-12' if datetime.utcnow() > datetime(2024, 12, 1) else datetime.utcnow().strftime('%Y-%m')
    month = request.args.get('month', default_month)
    month_date = datetime.strptime(month, '%Y-%m')
    
    budget = Budget.query.filter_by(user_id=current_user.id, month=month_date).first()
    if not budget:
        return render_template('budgets/dashboard.html', 
                             budget=None, 
                             datetime=datetime,
                             current_month=month)
    
    # Calculate total spent for the month
    total_spent = db.session.query(db.func.sum(Transaction.amount))\
        .filter_by(user_id=current_user.id, type='expense')\
        .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
    
    # Get category allocations and spending
    category_allocations = CategoryAllocation.query.filter_by(budget_id=budget.id).all()
    allocated_categories = [alloc.category_id for alloc in category_allocations]
    category_spending = {}
    
    # Calculate spending for allocated categories
    for allocation in category_allocations:
        spent = db.session.query(db.func.sum(Transaction.amount))\
            .filter_by(user_id=current_user.id, category_id=allocation.category_id, type='expense')\
            .filter(db.func.strftime('%Y-%m', Transaction.date) == month).scalar() or 0
        category_spending[allocation.category_id] = spent
    
    # Calculate spending for unallocated categories as "Others"
    others_spent = db.session.query(db.func.sum(Transaction.amount))\
        .filter_by(user_id=current_user.id, type='expense')\
        .filter(db.func.strftime('%Y-%m', Transaction.date) == month)\
        .filter(~Transaction.category_id.in_(allocated_categories)).scalar() or 0
    
    if others_spent > 0:
        category_spending['others'] = others_spent
    
    return render_template('budgets/dashboard.html', 
                         budget=budget, 
                         total_spent=total_spent, 
                         category_spending=category_spending,
                         category_allocations=category_allocations,
                         datetime=datetime,
                         current_month=month)

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
        year = int(request.form['year'])
        month = int(request.form['month'])
        month_date = datetime(year, month, 1)
        total_budget = float(request.form['total_budget'])
        
        # Check for overlapping budgets
        existing_budget = Budget.query.filter_by(user_id=current_user.id, month=month_date).first()
        if existing_budget:
            flash('A budget for this month already exists.', 'error')
            return redirect(url_for('budgets.list_budgets'))
        
        budget = Budget(
            user_id=current_user.id,
            month=month_date,
            total_budget=total_budget
        )
        db.session.add(budget)
        db.session.commit()
        
        # Add category allocations if provided
        category_ids = request.form.getlist('category_allocations[][category_id]')
        percentages = request.form.getlist('category_allocations[][percentage]')
        
        # Validate total percentage doesn't exceed 100%
        total_percentage = sum(float(p) for p in percentages if p)
        if total_percentage > 100:
            flash('Total category allocation percentage cannot exceed 100%.', 'error')
            db.session.delete(budget)
            db.session.commit()
            return redirect(url_for('budgets.list_budgets'))
        
        # Add valid category allocations
        for i, category_id in enumerate(category_ids):
            if category_id and percentages[i]:
                allocation = CategoryAllocation(
                    budget_id=budget.id,
                    category_id=int(category_id),
                    percentage=float(percentages[i])
                )
                db.session.add(allocation)
        
        db.session.commit()
        flash('Budget added successfully', 'success')
        
        if request.headers.get('HX-Request'):
            return """
            <script>
                document.getElementById('budget-modal').close();
                window.location.href = '{}';
            </script>
            """.format(url_for('budgets.list_budgets'))
        
        return redirect(url_for('budgets.list_budgets'))
    
    categories = Category.query.filter_by(user_id=current_user.id, type='expense').all()
    return render_template('budgets/_form.html', categories=categories, budget=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        budget.total_budget = float(request.form['total_budget'])
        
        # Update category allocations
        CategoryAllocation.query.filter_by(budget_id=budget.id).delete()
        
        # Get and validate new allocations
        category_ids = request.form.getlist('category_allocations[][category_id]')
        percentages = request.form.getlist('category_allocations[][percentage]')
        
        # Validate total percentage doesn't exceed 100%
        total_percentage = sum(float(p) for p in percentages if p)
        if total_percentage > 100:
            flash('Total category allocation percentage cannot exceed 100%.', 'error')
            db.session.rollback()
            return redirect(url_for('budgets.list_budgets'))
        
        # Add valid category allocations
        for i, category_id in enumerate(category_ids):
            if category_id and percentages[i]:
                allocation = CategoryAllocation(
                    budget_id=budget.id,
                    category_id=int(category_id),
                    percentage=float(percentages[i])
                )
                db.session.add(allocation)
        
        db.session.commit()
        flash('Budget updated successfully', 'success')
        
        if request.headers.get('HX-Request'):
            return """
            <script>
                document.getElementById('budget-modal').close();
                window.location.href = '{}';
            </script>
            """.format(url_for('budgets.list_budgets'))
        
        return redirect(url_for('budgets.list_budgets'))
    
    categories = Category.query.filter_by(user_id=current_user.id, type='expense').all()
    return render_template('budgets/_form.html', budget=budget, categories=categories)

@bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_budget(id):
    budget = Budget.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully', 'success')
    
    if request.headers.get('HX-Request'):
        budgets = Budget.query.filter_by(user_id=current_user.id).all()
        return render_template('budgets/_grid.html', budgets=budgets)
    
    return render_template('budgets/list.html', budgets=Budget.query.filter_by(user_id=current_user.id).all())
