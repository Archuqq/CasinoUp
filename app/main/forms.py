from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileRequired, FileAllowed

class PromoActivationForm(FlaskForm):
    code = StringField('Промокод', validators=[DataRequired(), Length(min=4, max=20)])
    submit = SubmitField('Активировать')

class DepositForm(FlaskForm):
    amount = FloatField('Сумма пополнения', validators=[
        DataRequired(),
        NumberRange(min=1, max=1000000, message='Сумма должна быть от 1₽ до 1,000,000₽')
    ])
    screenshot = FileField('Скриншот оплаты', validators=[
        FileRequired(message='Необходимо прикрепить скриншот'),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Разрешены только изображения (JPG, PNG)')
    ])
    comment = StringField('Комментарий к переводу', 
                        description='Укажите логин или email, который вы указали при переводе')
    submit = SubmitField('Отправить') 