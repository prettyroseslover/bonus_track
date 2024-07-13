from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class FurtherInfo(FlaskForm):
    surname = StringField("Фамилия", validators=[DataRequired()])
    name = StringField("Имя", validators=[DataRequired()])
    famname = StringField("Отчество", validators=[DataRequired()])
    phone_number = StringField("Телефон", validators=[DataRequired()])
    location = StringField("Адрес", validators=[DataRequired()])
    submit = SubmitField("Применить")


class BookFilter(FlaskForm):
    # japanese = BooleanField("Японский")
    # russian = BooleanField("Русский")
    # english = BooleanField("Английский")
    # scipop = BooleanField("Научпоп")
    # essay = BooleanField("Эссе")
    # stories = BooleanField("Рассказы")
    # cookbook = BooleanField("Кулинария")
    # novel = BooleanField("Роман")
    # narrative = BooleanField("Повесть")
    # japan = BooleanField("Япония")
    # china = BooleanField("Китай")
    # korea = BooleanField("Корея")
    # vietnam = BooleanField("Вьетнам")
    sort = SelectField('Сортировка', choices=[(0, "По умолчанию"), (1, "По убыванию цены"), (2, "По возрастанию цены")])
    submit = SubmitField("Применить")


class RatingBook(FlaskForm):
    #book = SelectField('ID книги', coerce=str)
    rating = SelectField('Оценка по шкале', coerce=int, choices=[(0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, "5"), (6, "6"), (7, "7"), (8, "8"), (9, "9"), (10, "10")])
    comment = TextAreaField('Рецензия')
    submit = SubmitField("Добавить!")


class CheckDiscount(FlaskForm):
    promocode = StringField("Промокод")
    submit = SubmitField("Применить!")


class RegistryForm(FlaskForm):
    username = StringField("Юзернейм", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Зарегистрироваться!")