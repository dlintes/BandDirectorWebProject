from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
#from sqlalchemy import Table, Column, Integer, ForeignKey
#from sqlalchemy.orm import relationship
#from sqlalchemy.ext.declarative import declarative_base

class Director(UserMixin, db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(255), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    ##role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Director %r>' % self.username


class Student(UserMixin, db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(255), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Student %r>' % self.username


class UploadFiles(UserMixin, db.Model):
    __tablename__ = 'upload_files'
    id = db.Column(db.Integer, primary_key=True)
    file_location = db.Column(db.String(255))
    file_name = db.Column(db.String(255))
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'))
    hw_create_time = db.Column(db.String(255))
    hw_id = db.Column(db.Integer, db.ForeignKey('homeworks.id'))

    def __repr__(self):
        return '<%r>' % self.file_name

class AddStudent(UserMixin, db.Model):
    __tablename__ = 'director_student'
    id = db.Column(db.Integer, primary_key=True)
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))

    def __repr__(self):
        return '<%r>' % self.director_id

@login_manager.user_loader
def load_director(director_id):
    return Director.query.get(int(director_id))

#@login_manager.student_loader
#def load_student(student_id):
#    return Student.query.get(int(student_id))

#@login_manager.upload_files_loader
#def load_upload_files(file_id):
#    return UploadFiles.query.get(int(file_id))
