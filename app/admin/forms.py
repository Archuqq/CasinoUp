from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateTimeField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange
from app.models import PromoCode

class UserBalanceForm(FlaskForm):
    balance = FloatField('Новый баланс', validators=[DataRequired()])
    submit = SubmitField('Обновить баланс')

class PromoCodeForm(FlaskForm):
    code = StringField('Код', validators=[DataRequired(), Length(min=4, max=20)])
    amount = FloatField('Сумма', validators=[DataRequired()])
    max_uses = IntegerField('Максимальное количество использований', 
                          validators=[DataRequired(), NumberRange(min=1)],
                          default=1)
    submit = SubmitField('Создать промокод')

    def validate_code(self, code):
        promo = PromoCode.query.filter_by(code=code.data).first()
        if promo:
            raise ValidationError('Этот промокод уже существует.') 