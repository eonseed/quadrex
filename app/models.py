from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from app.default_categories import DEFAULT_CATEGORIES
from sqlalchemy import UniqueConstraint

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    passkey_credential_id = db.Column(db.String(256), nullable=True)
    passkey_public_key = db.Column(db.String(512), nullable=True)
    passkey_sign_count = db.Column(db.Integer, default=0)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    budgets = db.relationship('Budget', backref='user', lazy=True)

    __table_args__ = (
        UniqueConstraint('passkey_credential_id', name='uq_user_passkey_credential_id'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_passkey(self):
        """Check if user has a passkey registered."""
        return bool(self.passkey_credential_id and self.passkey_public_key)

    def set_passkey(self, credential_id, public_key):
        """Set user's passkey credentials."""
        self.passkey_credential_id = credential_id
        self.passkey_public_key = public_key
        self.passkey_sign_count = 0

    def update_passkey_sign_count(self, new_count):
        """Update the sign count for passkey authentication."""
        self.passkey_sign_count = new_count

    def remove_passkey(self):
        """Remove user's passkey credentials."""
        self.passkey_credential_id = None
        self.passkey_public_key = None
        self.passkey_sign_count = 0

    def change_password(self, current_password, new_password):
        """Change user's password after verifying current password."""
        if not self.check_password(current_password):
            return False
        self.set_password(new_password)
        return True

    def create_default_categories(self):
        """Create default categories for the user."""
        for category_data in DEFAULT_CATEGORIES:
            category = Category(
                name=category_data['name'],
                type=category_data['type'],
                icon=category_data['icon'],
                user_id=self.id
            )
            db.session.add(category)
        db.session.commit()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    icon = db.Column(db.String(500))  # SVG path for the icon
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Make user_id required
    transactions = db.relationship('Transaction', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'icon': self.icon
        }

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(256))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'type': self.type,
            'category': self.category.to_dict()
        }

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month = db.Column(db.Date, nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_allocations = db.relationship('CategoryAllocation', backref='budget', lazy=True)

class CategoryAllocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    budget = db.relationship('Budget', backref='category_allocations')
