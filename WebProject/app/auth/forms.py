from flask_wtf import FlaskForm, Form
from flask_wtf import FlaskForm, Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, Form, FormField, FieldList, TextField, TextAreaField, DateField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo, InputRequired
from wtforms import ValidationError
from ..models import Director, Student, UploadFiles


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class StudentLoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

   # def validate_email(self, field):
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            print("Validating email")
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class DirectorRegistrationForm(FlaskForm):
    first_name = StringField('First name', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0,
                                          'First must have only letters, ')])
    last_name = StringField('Last name', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0,
                                          'First must have only letters, ')])
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if Director.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if Director.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class StudentRegistrationForm(FlaskForm):
    first_name = StringField('First name', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0,
                                          'First must have only letters, ')])
    last_name = StringField('Last name', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z]*$', 0,
                                          'First must have only letters, ')])
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                           Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    password = PasswordField('Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if Student.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if Student.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')

class AddStudentForm(FlaskForm):
    student_email = StringField('Email', validators=[Required(), Length(1, 64),Email()])
    add = SubmitField('Add')
    search = SubmitField('Search')

    def validate_student_email(self, field):
        if self.add.data == True:
            if Student.query.filter_by(email=field.data).first():
                raise ValidationError('Student is already registered.')
        if self.search.data == True:
            print("Search Student by email.")
            if not Student.query.filter_by(email=field.data).first():
                raise ValidationError('Student is not registered.')


class AssignFilesToStudents(FlaskForm):
    submit = SubmitField('Add')

class RowForm(FlaskForm):
    id = StringField('id')
    file_name = StringField('file_name')
    student_name = StringField('student_name')
    status = StringField('status')
    grade = StringField('grade')
    notes = StringField('notes', validators=[ Length(1, 64)])
    hw_name = StringField('hw_name')


class GridForm(FlaskForm):
    title = StringField('title')
    grid = FieldList(FormField(RowForm))

class ReqForm(FlaskForm):
    selected_file = StringField('id')
    submit = SubmitField('View selected file')

class SearchStudentForm(FlaskForm):
    student = StringField('id')
    submit = SubmitField('View selected file')

class EmailProfessorForm(FlaskForm):
    first_name = StringField('First name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    last_name = StringField('Last name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    email_subject = TextField('Subject')
    email_body = TextAreaField('Message')
    email = StringField('Email', validators=[Length(1, 64), Email()])
    submit = SubmitField('Send email')

    def validate_email(self, field):
        if len(field.data) > 0:
            if not Student.query.filter_by(email=field.data).first():
                raise ValidationError('Email not registered.')

class AddStudentToClassForm(FlaskForm):
    first_name = StringField('First name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    last_name = StringField('Last name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    email = StringField('Email', validators=[Length(1, 64), Email()])
    submit = SubmitField('Add student')

    """
    def validate_last_name(self, field):
        ##print("In validate class!")
        if not Student.query.filter_by(email=field.data).first():
            raise ValidationError('Email not registered.')

    def validate_email(self, field):
        ##print("In validate class!")
        if not Student.query.filter_by(email=field.data).first():
            raise ValidationError('Email not registered.')
    """

class SearchStudentsRowForm(FlaskForm):
    first_name = StringField('first_name')
    last_name = StringField('last_name')
    email = StringField('email')
    student_id = StringField('id')

class SearchStudentsGridForm(FlaskForm):
    title = StringField('title')
    grid = FieldList(FormField(SearchStudentsRowForm))

class StudentHomeworkRowForm(FlaskForm):
    file_name = StringField('file_name')
    hw_name = StringField('hw_name')

class StudentHomeworkGridForm(FlaskForm):
    title = StringField('title')
    grid = FieldList(FormField(StudentHomeworkRowForm))

class ProfessorForm(FlaskForm):
    first_name = StringField('First name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    last_name = StringField('Last name', validators=[
        Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'First names must have only letters.')])
    email = StringField('Email', validators=[Length(1, 64), Email()])
    submit = SubmitField('Retrieve homework')

class AddHomeworkForm(FlaskForm):
    hw_name = StringField('Homework name',  render_kw={"placeholder": "Enter homework"}, validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Homework names must have only letters,numbers, dots or underscores')])
    date_due = StringField(u'Date Due:', render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"},validators=[Required()])
    submit = SubmitField('Submit homework')

class ExtendDateForm(FlaskForm):
    date_due = StringField(u'Date Due:', render_kw={"placeholder": "YYYY-MM-DD HH:MM:SS"},validators=[Required()])
    submit = SubmitField('Submit date')

class ChoseMusicSheetNameForm(FlaskForm):
    file_name = StringField('File name',  render_kw={"placeholder": "Enter pattern file name"}, validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'File names must have only letters,numbers, dots or underscores')])
    out_file = StringField('Out file', render_kw={"placeholder": "Enter out file (PDF format)"}, validators=[
        Required(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'File names must have only letters,numbers, dots or underscores')])
    composer = StringField('Composer', render_kw={"placeholder": "Composer name"}, validators=[
        Required(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z]*$', 0, 'Names must have only letters and numbers.')])
    nr_notes = StringField('Notes', render_kw={"placeholder": "Enter number of notes to generate"}, validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z]*$', 0, 'Names must have only letters and numbers.')])
    submit = SubmitField('Generate music sheet')
    back = SubmitField('Back')

class ProfessorChangePwdForm(FlaskForm):
    new_pwd1 = PasswordField('Password', validators=[Required(), EqualTo('new_pwd2', message='Passwords must match.')])
    new_pwd2 = PasswordField('Confirm password', validators=[Required()])

    submit = SubmitField('Change password')

class StudentChangePwdForm(FlaskForm):
    new_pwd1 = PasswordField('Password', validators=[Required(), EqualTo('new_pwd2', message='Passwords must match.')])
    new_pwd2 = PasswordField('Confirm password', validators=[Required()])

    submit = SubmitField('Change password')