from flask import Blueprint

# Create the blueprint with url_prefix
bp = Blueprint('categories', __name__, url_prefix='/categories')

# Import routes after blueprint creation to avoid circular imports
from app.categories import routes
