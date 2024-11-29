import click
from flask.cli import with_appcontext
from app import db
from app.models import Category, User, Transaction
from app.default_categories import DEFAULT_CATEGORIES

def register_commands(app):
    app.cli.add_command(init_categories)
    app.cli.add_command(migrate_categories)

@click.command('init-categories')
@with_appcontext
def init_categories():
    """Initialize default categories."""
    users = User.query.all()
    for user in users:
        # Check if user already has categories
        if not Category.query.filter_by(user_id=user.id).first():
            for category_data in DEFAULT_CATEGORIES:
                category = Category(
                    name=category_data['name'],
                    type=category_data['type'],
                    icon=category_data['icon'],
                    user_id=user.id
                )
                db.session.add(category)
    db.session.commit()
    click.echo('Initialized default categories.')

@click.command('migrate-categories')
@with_appcontext
def migrate_categories():
    """Migrate global categories to user-specific categories."""
    try:
        # Find categories with null user_id
        null_user_categories = Category.query.filter_by(user_id=None).all()
        
        if null_user_categories:
            # Get all users
            users = User.query.all()
            
            # Create a mapping of old category IDs to new categories for each user
            category_mapping = {}  # {user_id: {old_category_id: new_category}}
            
            # For each user, create a copy of the null user categories
            for user in users:
                category_mapping[user.id] = {}
                for old_category in null_user_categories:
                    # Check if user already has a similar category
                    existing_category = Category.query.filter_by(
                        user_id=user.id,
                        name=old_category.name,
                        type=old_category.type
                    ).first()
                    
                    if existing_category:
                        # Use existing category
                        category_mapping[user.id][old_category.id] = existing_category
                    else:
                        # Create new category
                        new_category = Category(
                            name=old_category.name,
                            type=old_category.type,
                            icon=old_category.icon,
                            user_id=user.id
                        )
                        db.session.add(new_category)
                        db.session.flush()  # This will assign an ID to the new category
                        category_mapping[user.id][old_category.id] = new_category
            
            # Update transactions to use the new category IDs
            transactions = Transaction.query.filter(
                Transaction.category_id.in_([c.id for c in null_user_categories])
            ).all()
            
            click.echo(f'Found {len(transactions)} transactions to update.')
            
            for transaction in transactions:
                if transaction.user_id in category_mapping:
                    old_category_id = transaction.category_id
                    if old_category_id in category_mapping[transaction.user_id]:
                        new_category = category_mapping[transaction.user_id][old_category_id]
                        transaction.category_id = new_category.id
                    else:
                        click.echo(f'Warning: Could not find mapping for transaction {transaction.id} with category {old_category_id}')
                else:
                    click.echo(f'Warning: Could not find user mapping for transaction {transaction.id}')
            
            # Commit the transaction updates first
            db.session.commit()
            click.echo('Successfully updated transactions.')
            
            # Now delete the original null user categories
            for category in null_user_categories:
                db.session.delete(category)
            
            db.session.commit()
            click.echo('Successfully deleted global categories.')
            
            click.echo('Migration completed successfully.')
        else:
            click.echo('No global categories found. Nothing to migrate.')
            
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error during migration: {str(e)}', err=True)
        raise e
