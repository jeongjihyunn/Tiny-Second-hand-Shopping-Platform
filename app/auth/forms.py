from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp, EqualTo, ValidationError

USERNAME_RE = r"^[A-Za-z0-9_]{3,20}$"


class RegisterForm(FlaskForm):
    username = StringField("아이디", validators=[
        DataRequired(), Length(min=3, max=20),
        Regexp(USERNAME_RE, message="아이디는 영문/숫자/밑줄 3~20자만 가능합니다."),
    ])
    password = PasswordField("비밀번호", validators=[
        DataRequired(),
        Length(min=8, max=128, message="비밀번호는 8자 이상이어야 합니다."),
    ])
    confirm = PasswordField("비밀번호 확인", validators=[
        DataRequired(), EqualTo("password", message="비밀번호가 일치하지 않습니다."),
    ])
    submit = SubmitField("가입하기")

    def validate_password(self, field):
        pw = field.data
        classes = sum([
            any(c.islower() for c in pw),
            any(c.isupper() for c in pw),
            any(c.isdigit() for c in pw),
            any(not c.isalnum() for c in pw),
        ])
        if classes < 2:
            raise ValidationError("영문 대/소문자, 숫자, 특수문자 중 2가지 이상을 조합해주세요.")


class LoginForm(FlaskForm):
    username = StringField("아이디", validators=[DataRequired(), Length(max=20)])
    password = PasswordField("비밀번호", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("로그인")


class ProfileForm(FlaskForm):
    bio = TextAreaField("소개글", validators=[Length(max=500)])
    submit_profile = SubmitField("저장")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("현재 비밀번호", validators=[DataRequired()])
    new_password = PasswordField("새 비밀번호", validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField("새 비밀번호 확인", validators=[
        DataRequired(), EqualTo("new_password", message="비밀번호가 일치하지 않습니다."),
    ])
    submit_password = SubmitField("비밀번호 변경")
