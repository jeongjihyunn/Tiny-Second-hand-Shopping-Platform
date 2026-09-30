from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, StringField as MemoField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class TransferForm(FlaskForm):
    to_username = StringField("받는 사람 아이디", validators=[DataRequired(), Length(max=20)])
    amount = IntegerField("송금액", validators=[DataRequired(), NumberRange(min=1, max=100_000_000)])
    memo = MemoField("메모", validators=[Length(max=200)])
    submit = SubmitField("송금하기")
