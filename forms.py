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
    submit = SubmitField("Add to transactions")