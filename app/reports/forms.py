from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class ReportForm(FlaskForm):
    reason = TextAreaField("신고 사유", validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField("신고하기")
