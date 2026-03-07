from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, SubmitField
from wtforms.validators import InputRequired, EqualTo

class RegistrationForm(FlaskForm):
    user_id = StringField("User id: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])
    password2 = PasswordField("Confirm password: ", validators=[InputRequired(), EqualTo("password")])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    user_id = StringField("User id: ", validators=[InputRequired()])
    password = PasswordField("Password: ", validators=[InputRequired()])
    submit = SubmitField("Submit")

class TransactionForm(FlaskForm):
    currency = SelectField("Currency: ", choices=["EUR","CNY"], default="EUR")
    amount = FloatField("Amount: ", validators=[InputRequired()])
    type = SelectField("Type: ", choices=["income","expense"], default="expense")
    category = SelectField("Category: ", choices=["salary","food"], default="food")
    description = StringField("Description: ")
    submit = SubmitField("Add to transactions")

class SavingGoalForm(FlaskForm):
    goal_name = StringField("Goal name: ", validators=[InputRequired()])
    target_amount = FloatField("Target Amount: ", validators=[InputRequired()])
    currency = SelectField("Currency: ", choices=["EUR", "CNY"], validators=[InputRequired()])
    submit = SubmitField("Add")

class AddSavingForm(FlaskForm):
    amount = FloatField("Add Amount: ", validators=[InputRequired()])
    submit = SubmitField("Add")
