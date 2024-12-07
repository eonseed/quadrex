from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.budget import Budget
from app.models.category import Category
from app.forms.budget import BudgetForm
from sqlalchemy import extract
from datetime import datetime

bp = Blueprint('budgets', __name__)

@bp.route('/budgets', methods=['GET'])
@login_required
def list():
    form = BudgetForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    month = request.args.get('month', type=int) or datetime.utcnow().month
    year = request.args.get('year', type=int) or datetime.utcnow().year
    
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=month,
        year=year
    ).all()
    
    return render_template('budgets/list.html', budgets=budgets, form=form)

@bp.route('/budgets/add', methods=['POST'])
@login_required
def add():
    form = BudgetForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        existing_budget = Budget.query.filter_by(
            user_id=current_user.id,
            category_id=form.category_id.data,
            month=form.month.data,
            year=form.year.data
        ).first()
        
        if existing_budget:
            existing_budget.amount = form.amount.data
        else:
            budget = Budget(
                user_id=current_user.id,
                category_id=form.category_id.data,
                amount=form.amount.data,
                month=form.month.data,
                year=form.year.data
            )
            db.session.add(budget)
            
        db.session.commit()
        flash('Budget updated successfully', 'success')
        return redirect(url_for('budgets.list'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('budgets.list'))

@bp.route('/api/budgets/monthly', methods=['GET'])
@login_required
def get_monthly_data():
    month = request.args.get('month', type=int) or datetime.utcnow().month
    year = request.args.get('year', type=int) or datetime.utcnow().year
    
    budgets = Budget.query.filter_by(
        user_id=current_user.id,
        month=month,
        year=year
    ).all()
    
    budget_data = {
        'labels': [],
        'budgeted': [],
        'actual': []
    }
    
    for budget in budgets:
        budget_data['labels'].append(budget.category.name)
        budget_data['budgeted'].append(float(budget.amount))
        
        # Calculate actual spending for the category in this month
        actual = db.session.query(db.func.sum(Transaction.amount)).\
            filter(
                Transaction.category_id == budget.category_id,
                Transaction.user_id == current_user.id,
                extract('month', Transaction.date) == month,
                extract('year', Transaction.date) == year
            ).scalar() or 0.0
            
        budget_data['actual'].append(float(actual))
    
    return jsonify(budget_data)
