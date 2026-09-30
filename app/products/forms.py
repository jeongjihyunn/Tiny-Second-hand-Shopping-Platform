from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class ProductForm(FlaskForm):
    title = StringField("상품명", validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField("상품 설명", validators=[Length(max=2000)])
    price = IntegerField("가격", validators=[DataRequired(), NumberRange(min=0, max=100_000_000)])
    image = FileField("상품 사진", validators=[
        FileAllowed(["png", "jpg", "jpeg", "gif", "webp"], "이미지 파일만 업로드할 수 있습니다."),
    ])
    submit = SubmitField("등록")


class SearchForm(FlaskForm):
    q = StringField("검색어", validators=[Length(max=100)])
