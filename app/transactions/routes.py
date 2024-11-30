from flask import render_template, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Category
from app.transactions import bp
from datetime import datetime

@bp.route('/')
@login_required
def list():
    # Get filter parameters
    type_filter = request.args.get('type')
    category_id = request.args.get('category_id')
    
    # Build query
    query = Transaction.query.filter_by(user_id=current_user.id)
    
    if type_filter:
        query = query.filter_by(type=type_filter)
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    transactions = query.order_by(Transaction.date.desc()).all()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    if request.headers.get('HX-Request'):
        return render_template('transactions/_grid.html', 
                            transactions=transactions)
    
    return render_template('transactions/list.html',
                         transactions=transactions,
                         categories=categories)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        try:
            transaction = Transaction(
                description=request.form['description'],
                amount=float(request.form['amount']),
                type=request.form['type'],
                category_id=request.form['category_id'],
                date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
                user_id=current_user.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
            return render_template('transactions/_grid.html', transactions=transactions)
        except Exception as e:
            db.session.rollback()
            flash('Error adding transaction: ' + str(e), 'error')
            return render_template('transactions/_form.html', categories=categories), 422
    
    return render_template('transactions/_form.html', categories=categories)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    categories = Category.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        try:
            transaction.description = request.form['description']
            transaction.amount = float(request.form['amount'])
            transaction.type = request.form['type']
            transaction.category_id = request.form['category_id']
            transaction.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            
            db.session.commit()
            transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
            return render_template('transactions/_grid.html', transactions=transactions)
        except Exception as e:
            db.session.rollback()
            flash('Error updating transaction: ' + str(e), 'error')
            return render_template('transactions/_form.html', 
                                transaction=transaction, 
                                categories=categories), 422
    
    return render_template('transactions/_form.html', 
                         transaction=transaction,
                         categories=categories)

@bp.route('/<int:id>', methods=['DELETE'])
@login_required
def delete(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    try:
        db.session.delete(transaction)
        db.session.commit()
        return render_template('transactions/_grid.html',
                            transactions=Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
