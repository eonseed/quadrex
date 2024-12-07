from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime

class BudgetForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    month = SelectField('Month', coerce=int, validators=[DataRequired()], 
                       choices=[(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000)],
                       default=datetime.utcnow().year)
