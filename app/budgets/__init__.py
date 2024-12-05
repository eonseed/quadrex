from flask import Blueprint

bp = Blueprint('budgets', __name__, url_prefix='/budgets')

from app.budgets import routes
