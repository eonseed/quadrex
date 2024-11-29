from flask import Blueprint

# Create the blueprint with url_prefix
bp = Blueprint('transactions', __name__, url_prefix='/transactions')

# Import routes after blueprint creation to avoid circular imports
from app.transactions import routes
