from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Category
from app.categories import bp

@bp.route('/')
@login_required
def list():
    # Only show categories belonging to the current user
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('categories/list.html', categories=categories)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        category = Category(
            name=request.form['name'],
            type=request.form['type'],
            icon=request.form.get('icon', ''),
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully', 'success')
        return redirect(url_for('categories.list'))
    
    return render_template('categories/_form.html', 
                         action=url_for('categories.add'),
                         category=None)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.type = request.form['type']
        category.icon = request.form.get('icon', '')
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('categories.list'))
    
    return render_template('categories/_form.html',
                         action=url_for('categories.edit', id=id),
                         category=category)

@bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
def delete(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(category)
    db.session.commit()
    
    if request.headers.get('HX-Request'):
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template('categories/_grid.html', categories=categories)
    
    flash('Category deleted successfully', 'success')
    return redirect(url_for('categories.list'))
