import sys,os,datetime, time, operator
from calendar import timegm
from flask import render_template, redirect, request, url_for, flash,send_file, send_from_directory,current_app,g, session
from werkzeug import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .. import db
from ..models import Director, Student, UploadFiles, AddStudent
from ..email import send_email
from .forms import LoginForm, ReqForm, RegistrationForm, DirectorRegistrationForm, StudentRegistrationForm, AddStudentForm, \
    GridForm, RowForm, EmailProfessorForm, AddStudentToClassForm, SearchStudentsRowForm, SearchStudentsGridForm, ProfessorForm, \
    StudentHomeworkRowForm, StudentHomeworkGridForm, AddHomeworkForm, ExtendDateForm, ChoseMusicSheetNameForm, ProfessorChangePwdForm, \
    StudentChangePwdForm, StudentLoginForm
from sqlalchemy import text
from random import randint
import subprocess


from app import create_app
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
global g_director_id,g_student_id,g_director_name,g_student_name
g_director_id = None
g_director_name = None
g_student_id = None
g_student_name = None

with app.app_context():

    UPLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER')
    DOWNLOAD_FOLDER = current_app.config.get('UPLOAD_FOLDER')
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

global STATIC_FOLDER
STATIC_FOLDER = os.path.abspath("../" + "/static")

global char2notes
char2notes = {
    ' ': ("a4 a4 ", "r2 "),
    'a': ("<c a>2 ", "<e' a'>2 "),
    'b': ("e2 ", "e'4 <e' g'> "),
    'c': ("g2 ", "d'4 e' "),
    'd': ("e2 ", "e'4 a' "),
    'e': ("<c g>2 ", "a'4 <a' c'> "),
    'f': ("a2 ", "<g' a'>4 c'' "),
    'g': ("a2 ", "<g' a'>4 a' "),
    'h': ("r4 g ", " r4 g' "),
    'i': ("<c e>2 ", "d'4 g' "),
    'j': ("a4 a ", "g'4 g' "),
    'k': ("a2 ", "<g' a'>4 g' "),
    'l': ("e4 g ", "a'4 a' "),
    'm': ("c4 e ", "a'4 g' "),
    'n': ("e4 c ", "a'4 g' "),
    'o': ("<c a g>2  ", "a'2 "),
    'p': ("a2 ", "e'4 <e' g'> "),
    'q': ("a2 ", "a'4 a' "),
    'r': ("g4 e ", "a'4 a' "),
    's': ("a2 ", "g'4 a' "),
    't': ("g2 ", "e'4 c' "),
    'u': ("<c e g>2  ", "<a' g'>2"),
    'v': ("e4 e ", "a'4 c' "),
    'w': ("e4 a ", "a'4 c' "),
    'x': ("r4 <c d> ", "g' a' "),
    'y': ("<c g>2  ", "<a' g'>2"),
    'z': ("<e a>2 ", "g'4 a' "),
    '\n': ("r1 r1 ", "r1 r1 "),
    ',': ("r2 ", "r2"),
    '.': ("<c e a>2 ", "<a c' e'>2")}

@auth.route('/DirectorLogin', methods=['GET', 'POST'])
def DirectorLogin():
    """ Director login page."""
    global g_director_id, g_director_name
    form = LoginForm()
    if form.validate_on_submit():
        user = Director.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            director = Director.query.filter_by(email=form.email.data).first()
            g_director_id = director.id
            g_director_name = director.first_name + " " + director.last_name
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('auth.DirectorMenu'))
        flash('Invalid username or password.')
    return render_template('auth/DirectorLogin.html', form=form)

@auth.route('/StudentLogin', methods=['GET', 'POST'])
def StudentLogin():
    """ Student login page. """
    global g_student_id
    form = StudentLoginForm()
    if form.validate_on_submit():
        user = Student.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            g_student_id = user.id
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('auth.StudentMenu'))
        flash('Invalid username or password.')
    return render_template('auth/StudentLogin.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/RegisterDirector', methods=['GET', 'POST'])
def RegisterDirector():
    """ Function to add a new professor to the DB along with the required info. """
    form = DirectorRegistrationForm()
    if form.validate_on_submit():
        director = Director(first_name=form.first_name.data,
                       last_name=form.last_name.data,
                        email=form.email.data,
                        username=form.username.data,
                        password=form.password.data)
        db.session.add(director)
        flash('You can now login.')
        return redirect(url_for('auth.DirectorLogin'))
    return render_template('auth/RegisterDirector.html', form=form)

@auth.route('/RegisterStudent', methods=['GET', 'POST'])
def RegisterStudent():
    """ Function to add a new student to the DB along with the required info. """
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        student = Student(first_name=form.first_name.data,
                       last_name=form.last_name.data,
                       email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(student)
        flash('You can now login.')
        return redirect(url_for('auth.StudentLogin'))
    return render_template('auth/RegisterStudent.html', form=form)

def allowed_file(filename):
    """ Filtering the file types allowed to be uploaded. """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route("/upload", methods=['GET', 'POST'])
def upload():
    """ Builds a list of available homeworks to be passed to a drop down list in the upload page. """
    hw_list = []
    sql = ("select hw_name from web.homeworks where director_id = " + str(g_director_id))
    result = db.engine.execute(sql)
    for row in result:
        hw_list.append(row[0])
    return render_template('auth/upload.html', hw_list = hw_list)

@auth.route('/uploader', methods = ['GET', 'POST'])
def uploader():
   if request.method == 'POST':
      sql = ("select id from web.homeworks where director_id = " + str(g_director_id) + " and hw_name = '" + request.form['homework'] + "'")
      result = db.engine.execute(sql)
      for row in result:
          hw_id = row[0]

      f = request.files['file']
      filename = secure_filename(f.filename)
      STATIC_FOLDER = os.path.abspath("../" + "/static")
      f.save(os.path.join(STATIC_FOLDER, filename))

      file_upd_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      R_STATIC_FOLDER = STATIC_FOLDER.replace('\\', '\\\\')
      sql = ("select id from web.upload_files where director_id = " + str(g_director_id) + "  and hw_id = " + str(hw_id) + " and file_name = '" + filename + "' and file_location = '" + R_STATIC_FOLDER + "'")
      result = db.engine.execute(sql)
      rec_id = None
      for row in result:
          rec_id = row[0]
      if rec_id is not None:
          sql = ("update web.upload_files set file_upd_time = '" + file_upd_time + "' where id = " + str(rec_id))
          db.engine.execute(sql)
          flash("File is already loaded. Changed update time.")
          return redirect(url_for('auth.upload'))

      sql = ("insert into web.upload_files (file_name, file_location, director_id, file_upd_time, hw_id) values('" + filename + "','" + R_STATIC_FOLDER + "'," + str(g_director_id) + ",'" + file_upd_time + "'," + str(hw_id) + ")")
      db.engine.execute(sql)
      flash('File uploaded successfully')
      return redirect(url_for('auth.upload'))

@auth.route("/ChoseProfessor", methods=['GET', 'POST'])
def ChoseProfessor():
    global g_professor_id
    professor_list = []
    sql =  ("select CONCAT(d.first_name, ' ', d.last_name, ' - ', d.email) "
            "from web.director d "
            "join web.director_student ds on ds.director_id = d.id "
            " where ds.student_id = " + str(g_student_id))

    result = db.engine.execute(sql)
    for row in result:
        professor_list.append(row[0])

    if request.method == 'POST':
        professor_name = request.form['professor']
        professor_email = professor_name.split("-")[1].strip()
        sql = ("select id from web.director where email = '" + professor_email + "'")
        result = db.engine.execute(sql)
        for row in result:
            g_professor_id = row[0]
        hw_list = []
        sql = ("select hw_name from web.homeworks where director_id  = " + str(g_professor_id))
        result = db.engine.execute(sql)
        for row in result:
            hw_list.append(row[0])
        return render_template('auth/UploadStudentFiles.html',hw_list = hw_list)
    return render_template('auth/ChoseProfessor.html', professor_list = professor_list)

@auth.route("/UploadStudentFiles", methods=['GET', 'POST'])
def UploadStudentFiles():
    return render_template('auth/UploadStudentFiles.html')

@auth.route('/StudentFileUploader', methods = ['GET', 'POST'])
def StudentFileUploader():
   """ Inserts student files in the database. Called from UploadStudentFiles.html. """
   if request.method == 'POST':
      hw_name = request.form['homework']
      sql = ("select id,hw_deadline from web.homeworks where director_id = " + str(g_professor_id) + " and hw_name = '" + hw_name.strip() + "'")
      result = db.engine.execute(sql)
      for row in result:
            hw_id = row[0]
            hw_deadline = row[1]

      current_time_epoch = int(time.time())
      utc_time = time.strptime(str(hw_deadline), "%Y-%m-%d %H:%M:%S")
      hw_deadline_epoch = timegm(utc_time)
      if current_time_epoch > hw_deadline_epoch:
          flash("Current time is past deadline: " + str(hw_deadline) + ". Homework cannot be uploaded.")
          return redirect(url_for('auth.ChoseProfessor'))

      f = request.files['file']
      filename = secure_filename(f.filename)
      STATIC_FOLDER = os.path.abspath("../" + "/static")
      R_STATIC_FOLDER = STATIC_FOLDER.replace('\\', '\\\\')
      f.save(os.path.join(STATIC_FOLDER, filename))
      sql = text("select id,reviewed from web.student_files where file_name = '" + str(filename) +\
                 "' and file_location = '" + R_STATIC_FOLDER + "' and student_id = " +\
                 str(g_student_id) + " and director_id = " +str(g_professor_id) + " and hw_id = " + str(hw_id))
      result = db.engine.execute(sql)
      rec_id = None
      for row in result:
          rec_id = row[0]
          reviewed = row[1]
      if rec_id is not None:
          if reviewed == 1:
            # if file has not been reviewied we let the student upload the file again
            sql = text('delete from web.student_files where id = ' + str(rec_id) + '')
            db.engine.execute(sql)
            sql = text('insert into web.student_files (file_name,file_location,student_id,hw_id,director_id) values(\'' + filename + '\',\'' + R_STATIC_FOLDER + '\',' + str(g_student_id) + ',' + str(hw_id) + ',' +str(g_professor_id) + ')')
            result = db.engine.execute(sql)
          else:
              flash("File has been reviewed. Cannot upload another version.")
              return redirect(url_for('auth.ChoseProfessor'))
      else:
          sql = text('insert into web.student_files (file_name,file_location,student_id,hw_id,director_id) values(\'' + filename + '\',\'' + R_STATIC_FOLDER + '\',' + str(g_student_id) + ',' + str(hw_id) + ',' +str(g_professor_id) + ')')
          result = db.engine.execute(sql)
      flash("'File: " + filename + " uploaded successfully'")
      return redirect(url_for('auth.ChoseProfessor'))

@auth.route("/DeleteStudent/<student_id>", methods=['GET', 'POST'])
def DeleteStudent(student_id):
    """ Function to add a student to a class. The professor adds a student to his/her class. """
    ##form = AddStudentToClassForm()
    student = {}
    ##student['name'] = "name"
    ##student['student_id'] = student_id

    studentId = student_id.split("=")[-1]
    studentId = int(studentId.replace("\"", '').replace('>', ''))
    sql = ("delete from web.director_student where director_id = " + str(g_director_id) + " and student_id = " + str(studentId))
    result = db.engine.execute(sql)

    return redirect(url_for('auth.SearchStudents'))

@auth.route("/AddStudent", methods=['GET', 'POST'])
def AddStudent():
    """ Function to add a student to a class. The professor adds a student to his/her class. """
    print(g_director_id) ##
    global studentId
    student_list = []
    dctStudent = {}
    sql =  ("select  CONCAT(CONCAT(first_name, ' ', last_name), ' - ', email) as firstlast "
            "from web.student "
            "where id not in (select student_id from web.director_student where director_id = " + str(g_director_id) + ")")
    result = db.engine.execute(sql)
    for row in result:
        student_list.append(row[0])
    if request.method == 'POST':
        if request.form['btn'] == 'Add Student':
            if not ('student' in request.form.keys()):
                return "No student was selected."

            studentEmail = request.form['student'].split('-')[1].strip()
            sql = "select id from web.student where email = '" + studentEmail + "'"
            result = db.engine.execute(sql)
            studentId = None
            for row in result:
                studentId = row[0]
            if studentId is not None:
                sql = ("insert into web.director_student (director_id,student_id) values(" + str(g_director_id) + "," + str(studentId) + ")")
                try:
                    result = db.engine.execute(sql)
                except Exception as err:
                    return "Error: " + str(format(err))
            else:
                return "Could not retrieve student with email: " + studentEmail
        return redirect(url_for('auth.SearchStudents'))

    return render_template('auth/AddStudent.html', student_list=student_list)

# Inserts student files in the database. Called from UploadStudentFiles.html
@auth.route('/AssignFile', methods = ['GET', 'POST'])
def AssignFile():
    if request.method == 'POST':
        selected_file_id = file_id_dict[request.form['file']]
        if request.form['student'] != 'ALL':
            selected_student_id = student_id_dict[request.form['student']]
            sql = ("select count(*) from web.dir_student_files where director_id = " + str(g_director_id) + " and student_id = " + str(selected_student_id) + " and file_id = " +str(selected_file_id))
            result = db.engine.execute(sql)
            for row in result:
                if row[0] > 0:
                    flash("File id: " + str(selected_file_id) + " has already been assigned to this student.")
                    return redirect(url_for('auth.ChoseFileToAssign'))
            # we can safely insert now as we verified earlier that the record doesn't exist.
            sql = ("insert into web.dir_student_files (director_id,student_id,file_id) values(" + str(g_director_id) + "," +str(selected_student_id) + "," + str(selected_file_id) + ")")
            result = db.engine.execute(sql)
        else:
            sql = ("select id from web.student "
                   "where id in (select student_id from web.director_student where director_id = " + str(g_director_id) + ")")
            student_ids = db.engine.execute(sql)
            for id in student_ids:
                sql = ("select count(*) from web.dir_student_files where director_id = " + str(
                    g_director_id) + " and student_id = " + str(id[0]) + " and file_id = " + str(
                    selected_file_id))
                result = db.engine.execute(sql)
                for row in result:
                    if row[0] > 0:
                        flash("File id: " + str(selected_file_id) + " has already been assigned to student id: " + str(row[0]))
                        continue
                    else:
                        # we can safely insert now as we verified earlier that the record doesn't exist.
                        sql = ("insert into web.dir_student_files (director_id,student_id,file_id) values(" + str(
                            g_director_id) + "," + str(id[0]) + "," + str(selected_file_id) + ")")
                        result = db.engine.execute(sql)
                        flash("File id: " + str(selected_file_id) + " has been assigned successfully")
    return redirect(url_for('auth.ChoseFileToAssign'))

@auth.route("/ChoseFileToAssign", methods=['GET', 'POST'])
def ChoseFileToAssign():
    """ Picks the file to be assigned to a student. """
    global file_id_dict,student_id_dict
    file_id_dict = {}
    student_id_dict = {}
    hw_list = []
    sql = ("select hw_name from web.homeworks where director_id = " + str(g_director_id))
    result = db.engine.execute(sql)
    for row in result:
        hw_list.append(row[0])

    if request.method == 'POST':
        file_list = []
        student_list = []
        hw_name = request.form['homework']
        sql = ("select id from web.homeworks where hw_name = '" + hw_name + "' and director_id = " + str(g_director_id))
        result = db.engine.execute(sql)
        for row in result:
            hw_id = row[0]
        sql = ("select file_name,id from web.upload_files where director_id  = " + str(g_director_id) + " and hw_id = " + str(hw_id))
        result = db.engine.execute(sql)
        for row in result:
            file_list.append(row[0])
            file_id_dict[row[0]] = row[1]

        sql = ("select CONCAT(first_name,' ',last_name), id from web.student st "
               "where st.id in (select student_id from web.director_student ds where director_id = " + str(g_director_id) + ")")
        result = db.engine.execute(sql)
        for row in result:
            student_list.append(row[0])
            student_id_dict[row[0]] = row[1]
        student_list.append("ALL")
        return render_template('auth/AssignFilesToStudents.html',file_list = file_list, student_list = student_list)
    return render_template('auth/ChoseFileToAssign.html', hw_list = hw_list)

@auth.route("/UpdateStudentPermissions", methods=['GET', 'POST'])
def UpdateStudentPermissions():
    # Update database records
    return redirect(url_for('auth.AddStudent'))

@auth.route("/ShowFiles", methods=['GET', 'POST'])
def show_files():
    sql = text('select file_name from upload_files where director_id in \
       (select director_id from web.director_student where student_id = ' + str(g_student_id) +')')
    result = db.engine.execute(sql)
    fileList =[]
    for row in result:
        fileList.append(row[0])
    return render_template('auth/ShowFiles.html', fileList=fileList)

# To be deployed later
@auth.route("/PracticeMusic", methods=['GET', 'POST'])
def PracticeMusic():
    sql = ("select uf.file_name, uf.director_id, uf.hw_id, d.first_name, d.last_name, h.hw_name "
           "from web.upload_files as uf join web.director as d on uf.director_id = d.id "
           "join web.homeworks as h on uf.hw_id = h.id "
           "where RIGHT(uf.file_name,4) = '.mid' and uf.director_id in "
           "(select director_id from web.dir_student_files where student_id = " + str(g_student_id) + ")")
    print("SQL: ", sql)
    result = db.engine.execute(sql)
    fileList = []
    for row in result:
        dctFile = {}
        dctFile['file_name'] = row[0]
        dctFile['director_id'] = row[1]
        dctFile['hw_id'] = row[2]
        dctFile['first_name'] = row[3]
        dctFile['last_name'] = row[4]
        dctFile['hw_name'] = row[5]
        fileList.append(dctFile)
    print(fileList)

    return render_template('auth/PracticeMusic.html', files = fileList)

@auth.route("/PlayMidiFile/<file_name>", methods=['GET', 'POST'])
def PlayMidiFile(file_name):
    """ Function to play a midi file from the ones assigned to the student. """
    print(file_name)
    cmd = 'start ' + STATIC_FOLDER + '\\' + str(file_name.strip())
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = proc.communicate()
    return redirect(url_for('auth.PracticeMusic'))

"""
@auth.route("/ProfessorReviewFiltered/<filter_type>", methods=['GET', 'POST'])
def ProfessorReviewFiltered(filter_type):
    print(filter_type)
    ##cmd = 'start ' + STATIC_FOLDER + '\\' + str(file_name.strip())
    ##proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ##(out, err) = proc.communicate()
    return redirect(url_for('auth.ProfessorReviewFiles'))

# To be deployed later
@auth.route("/UploadNewRecording", methods=['GET', 'POST'])
def UploadNewRecording():
    pass # place holder
    return render_template('auth/UploadNewRecording.html')
"""

@auth.route("/EmailProfessor", methods=['GET', 'POST'])
def EmailProfessor():
    """ Function to send email to selected professor. """
    form = EmailProfessorForm()
    if request.method == 'POST':
        if len(form.data['email'].strip()) > 0:
            # Email has already been validated. Send email.
            email = form.data['email'].strip()
            sql = ("select count(*) "
                   "from web.director "
                   "where email = '" + str(email)) + "'"
            result = db.engine.execute(sql)
            if result is not None:
                for row in result:
                    nr_rec = row[0]
                if nr_rec == 0:
                    return "There are no registered users having email: " + email
                elif nr_rec > 1:
                    return "There are multiple registered users having email: " + email
        else:
            first_name = form.data['first_name'].strip()
            last_name = form.data['last_name'].strip()
            if (len(first_name) > 0) and (len(last_name) > 0):
                sql = ("select email "
                       "from web.director "
                       "where first_name = '" + str(first_name)) + "' and last_name = '" + str(last_name) +"'"
                result = db.engine.execute(sql)
                if result is not None:
                    if result.rowcount == 1:
                        for row in result:
                            email = row[0]
                    else:
                        if result.rowcount == 0:
                            return "There are no registered users having first name: " + str(first_name) + " and last name: " +  str(last_name)
                        return "There are more than one registered users having first name: " + str(first_name) + " and last name: " + str(last_name)
        # If we reach this line, we have a valid email
        send_email(email, 'Test message', 'This is a test message.', user='NewUser')
        return redirect(url_for('auth.EmailProfessor'))
    return render_template('auth/EmailProfessor.html', form = form)

@auth.route("/DirectorMenu", methods=['GET', 'POST'])
def DirectorMenu():
    """ Implements director menu. Starting point for all professor related menu options. """
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            return redirect(url_for('auth.DirectorMenu'))
    return render_template('auth/DirectorMenu.html')

@auth.route("/ProfessorReviewFiles/<filter_type>", methods=['GET', 'POST'])
def ProfessorReviewFiles(filter_type):
    """ Function to allow professor to review files uploaded by students. """
    print("Filter type: ", filter_type)
    submitForm = ReqForm()
    teamform = GridForm()
    teamform.title.data = g_director_name
    if (filter_type == 'A'):
        sql = ("select sf.id, sf.file_name, CONCAT(st.first_name, ' ', st.last_name), sf.reviewed, sf.grade,sf.notes, hw.hw_name "
            "from web.student_files sf "
            "join web.student st on sf.student_id = st.id "
            "join web.director_student ds on sf.student_id = ds.student_id "
            "join web.homeworks hw on sf.hw_id = hw.id "
            "where ds.director_id = " + str(g_director_id) + " and sf.director_id = " + str(g_director_id) + " "
            "order by sf.reviewed DESC")
    elif (filter_type == 'R'):
        sql = ("select sf.id, sf.file_name, CONCAT(st.first_name, ' ', st.last_name), sf.reviewed, sf.grade,sf.notes, hw.hw_name "
            "from web.student_files sf "
            "join web.student st on sf.student_id = st.id "
            "join web.director_student ds on sf.student_id = ds.student_id "
            "join web.homeworks hw on sf.hw_id = hw.id "
            "where ds.director_id = " + str(g_director_id) + " and sf.director_id = " + str(g_director_id) + " "
            "and sf.reviewed = 0 order by sf.reviewed DESC")
    else:
        sql = ("select sf.id, sf.file_name, CONCAT(st.first_name, ' ', st.last_name), sf.reviewed, sf.grade,sf.notes, hw.hw_name "
            "from web.student_files sf "
            "join web.student st on sf.student_id = st.id "
            "join web.director_student ds on sf.student_id = ds.student_id "
            "join web.homeworks hw on sf.hw_id = hw.id "
            "where ds.director_id = " + str(g_director_id) + " and sf.director_id = " + str(g_director_id) + " "
            "and sf.reviewed = 1 order by sf.reviewed DESC")

    result = db.engine.execute(sql)

    file_list = []
    for member in result:
        member_form = RowForm()
        member_form.id = str(member[0])
        member_form.file_name = member[1]
        member_form.student_name = member[2]
        if member[3] == 0:
            member_form.status = 'REVIEWED'
        else:
            member_form.status = 'NOT REVIEWED'
        member_form.grade = member[4]
        member_form.notes = member[5]
        member_form.hw_name = member[6]

        file_list.append(member[1])
        teamform.grid.append_entry(member_form)

    if request.method == 'POST':
        selected_file = request.form['file']
        if request.form['btn'] == 'Review file':
            sql = ("update web.student_files set reviewed = 0, updated = NOW() where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)
            STATIC_FOLDER = os.path.abspath("../" + "/static")
            return send_from_directory(directory=STATIC_FOLDER, filename=selected_file)
        if request.form['btn'] == 'Grade':
            if request.form['grade'] is None or len(request.form['grade']) == 0:
                ##return "Grade has to be between 0 and 100"
                flash("Grade has to be between 0 and 100")
                return redirect(url_for("auth.ProfessorReviewFiles", filter_type=filter_type))
            sql = ("update web.student_files set grade = " + str(request.form['grade']) + ", time_graded = NOW() where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)
            if request.form['notes'] is not None:
                sql = ("update web.student_files set notes = '" + str(request.form['notes']) + "' where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)

        return redirect(url_for("auth.ProfessorReviewFiles",filter_type=filter_type))
    return render_template('auth/ProfessorReviewFiles.html', teamform = teamform, submitForm = submitForm,file_list = file_list)

@auth.route("/SearchStudents", methods=['GET', 'POST'])
def SearchStudents():
    """ List students assigned to a class/professor. """
    search_student_form = SearchStudentsGridForm()
    search_student_form.title.data = str(g_director_name)

    sql =   ("select st.first_name, st.last_name, st.email, st.id "
        "from web.student st "
        "   join web.director_student ds on st.id = ds.student_id "
        "where ds.director_id = " +str(g_director_id))
    result = db.engine.execute(sql)
    for member in result:
        member_form = SearchStudentsRowForm()
        member_form.first_name = member[0]
        member_form.last_name = member[1]
        member_form.email = member[2]
        member_form.student_id = member[3]
        search_student_form.grid.append_entry(member_form)

    return render_template('auth/SearchStudents.html', search_student_form = search_student_form)

@auth.route("/Daria", methods=['GET', 'POST'])
def Daria():
    if request.method == 'POST':
        return redirect(url_for('auth.Daria'))
    return render_template('auth/Daria.html')

@auth.route("/StudentMenu", methods=['GET', 'POST'])
def StudentMenu():
    if request.method == 'POST':
        return redirect(url_for('auth.StudentMenu'))
    return render_template('auth/StudentMenu.html')

@auth.route("/SearchProfessor", methods=['GET', 'POST'])
def SearchProfessor():
    global g_professor_id
    form = ProfessorForm()
    if request.method == 'POST':
        if len(request.form['email']) > 0:
            sql =  ("select id from web.director where email = '" + str(request.form['email']) + "'")
            result = db.engine.execute(sql)
            if result is not None:
                for row in result:
                    g_professor_id = row[0]
                    session['professor_id'] = row[0]
        return redirect(request.args.get('next') or url_for('auth.StudentReviewHomework'))
    return render_template('auth/SearchProfessor.html', form = form)

@auth.route("/StudentReviewHomework", methods=['GET', 'POST'])
def StudentReviewHomework():
    """ Implements logic for the student to review files (homework) assigned by a professor. """
    s_professor_id = session.get('professor_id')
    sql = ("select CONCAT(first_name, ' ', last_name) from web.director where id = " + str(s_professor_id))
    result = db.engine.execute(sql)
    professor_name = ""
    for row in result:
        professor_name = row[0]

    form = StudentHomeworkGridForm()
    form.title.data = professor_name

    sql =   ("select uf.file_name, hw.hw_name "
            "from web.upload_files uf "
            "join web.director d on d.id = uf.director_id "
            "join web.dir_student_files dsf on dsf.file_id = uf.id "
            "join web.homeworks hw on uf.hw_id = hw.id "
            "where d.id = " + str(g_professor_id) + " and dsf.student_id = " + str(g_student_id))

    result = db.engine.execute(sql)

    file_list = []
    for member in result:
        member_form = StudentHomeworkRowForm()
        member_form.file_name = str(member[0])
        member_form.hw_name = member[1]
        file_list.append(str(member[0]))
        form.grid.append_entry(member_form)

    if request.method == 'POST':
        selected_file = request.form['file']
        if request.form['btn'] == 'Review file':
            STATIC_FOLDER = os.path.abspath("../" + "/static")
            return send_from_directory(directory=STATIC_FOLDER, filename=selected_file)
        return redirect(url_for('auth.StudentReviewHomework'))
    return render_template('auth/StudentReviewHomework.html', StudentHomeworkGridForm = form,file_list = file_list)

@auth.route("/ProfessorAddHomework", methods=['GET', 'POST'])
def ProfessorAddHomework():
    """ Function to upload homework. """
    form = AddHomeworkForm()
    if request.method == 'POST':
        hw_name = request.form['hw_name']
        sql = ("select count(*) from web.homeworks where director_id = " + str(g_director_id) + " and hw_name = '" + hw_name + "'")
        result = db.engine.execute(sql)
        for row in result:
            rec_count = row[0]
        if rec_count > 0:
            return "There is already a homework called: " + hw_name + " for professor id: " + str(g_director_id)
        date_due = request.form['date_due']
        sql = ("insert into web.homeworks (director_id,hw_name,hw_deadline) values (" + str(g_director_id) + ",'" + hw_name + "','" + date_due.strip() + "')")
        result = db.engine.execute(sql)

        hw_dict = {}
        sql = ("select hw_name,hw_deadline from web.homeworks where director_id = " + str(g_director_id))
        result = db.engine.execute(sql)
        for row in result:
            hw_dict[row[0]] = row[1]
        return redirect(url_for('auth.Homework'))

    return render_template('auth/ProfessorAddHomework.html', form = form)

@auth.route("/ExtendHomeworkDueDate", methods=['GET', 'POST'])
def ExtendHomeworkDueDate():
    """ Logic to allow professor to extend homework dead line. """
    form = ExtendDateForm()
    if request.method == 'POST':
        hw_due_date = request.form['date_due']
        sql = ("update homeworks set hw_deadline = '" + str(hw_due_date) + "' where director_id = " + str(g_director_id) + " and hw_name = '" + g_hw_name + "'")
        result = db.engine.execute(sql)
    return render_template('auth/ExtendHomeworkDueDate.html', form = form)

@auth.route("/ProfessorDeleteHomework", methods=['GET', 'POST'])
def ProfessorDeleteHomework():
    """ Logic to allow professor to delete a homework and all the records associated. """
    sql = "select id from web.homeworks where hw_name = '" + g_hw_name + "'"
    result = db.engine.execute(sql)
    hw_id = None
    for row in result:
        hw_id = row[0]

    if hw_id is not None:
        sql = "delete from web.upload_files where hw_id = " +str(hw_id)
        db.engine.execute(sql)

        sql = "delete from web.student_files where hw_id = " +str(hw_id)
        db.engine.execute(sql)

        sql = "delete from web.homeworks where id = " +str(hw_id)
        db.engine.execute(sql)

    hw_dict = {}
    sql = ("select hw_name,hw_deadline from web.homeworks where director_id = " + str(g_director_id))
    result = db.engine.execute(sql)
    for row in result:
        hw_dict[row[0]] = row[1]

    return redirect(url_for('auth.Homework'))

@auth.route("/Homework", methods=['GET', 'POST'])
def Homework():
    global g_hw_name
    hw_dict = {}
    sql = ("select hw_name,hw_deadline from web.homeworks where director_id = " + str(g_director_id))
    result = db.engine.execute(sql)
    for row in result:
        hw_dict[row[0]] = row[1]
    if request.method == 'POST':
        if request.form['btn'] == 'Add':
            return redirect(request.args.get('next') or url_for('auth.ProfessorAddHomework'))
        if request.form['btn'] == 'Extend due date':
            g_hw_name = request.form['homework']
            return redirect(request.args.get('next') or url_for('auth.ExtendHomeworkDueDate'))
        if request.form['btn'] == 'Delete':
            g_hw_name = request.form['homework']
            return redirect(request.args.get('next') or url_for('auth.ProfessorDeleteHomework'))

    return render_template('auth/Homework.html', hw_dict = hw_dict)

@auth.route("/StudentChoseProfessorReviewHomework", methods=['GET', 'POST'])
def StudentChoseProfessorReviewHomework():
    global g_professor_id
    professor_list = []
    sql =  ("select CONCAT(d.first_name, ' ', d.last_name, ' - ', d.email) "
            "from web.director d "
            "join web.director_student ds on ds.director_id = d.id "
            " where ds.student_id = " + str(g_student_id))

    result = db.engine.execute(sql)
    for row in result:
        professor_list.append(row[0])
    if request.method == 'POST':
        professor_name = request.form['professor']
        professor_email = professor_name.split("-")[1].strip()
        sql = ("select id from web.director where email = '" + professor_email + "'")
        result = db.engine.execute(sql)
        for row in result:
            g_professor_id = row[0]
            session['professor_id'] = row[0]
        return redirect(request.args.get('next') or url_for('auth.StudentReviewHomework'))
    return render_template('auth/StudentChoseProfessorReviewHomework.html', professor_list=professor_list)

# Password change. @login_required decorator will confirm that we are already logged in. No need to verify old password
@auth.route("/ProfessorChangePwd", methods=['GET', 'POST'])
@login_required
def ProfessorChangePwd():
    """ Function to upload homework. """
    form = ProfessorChangePwdForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = current_user
            user.password = form.new_pwd1.data
            db.session.add(user)
            db.session.commit()
            flash('Password has been updated!', 'success')
            return redirect(url_for('auth.DirectorLogin'))

    return render_template('auth/ProfessorChangePwd.html', form = form)

# Password change. @login_required decorator will confirm that we are already logged in. No need to verify old password
@auth.route("/StudentChangePwd", methods=['GET', 'POST'])
@login_required
def StudentChangePwd():
    """ Function to upload homework. """
    form = StudentChangePwdForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            ##load_student(student_id)
            ##user = current_user
            ##user = Student.query.filter_by(email=form.email.data).first()
            ##ser = Student.query.filter_by(id=g_student_id)
            user = Student.query.get(int(g_student_id))
            user.password = form.new_pwd1.data
            db.session.add(user)
            db.session.commit()
            flash('Password has been updated!', 'success')
            return redirect(url_for('auth.StudentLogin'))

    return render_template('auth/StudentChangePwd.html', form = form)

@auth.route("/GenerateMusic", methods=['GET', 'POST'])
def GenerateMusic():
    """ This section starts from a phrase and generates music using LilyPond and converts it into
        a PDF file that will be stored in the standard static location.
    """

    form = ChoseMusicSheetNameForm(nr_notes = 1000)
    if request.method == 'POST':
        try:
            if 'back' in request.form.keys():
                return redirect(url_for('auth.DirectorMenu'))
            patternFile = request.form['file_name']
            lilyFile = request.form['out_file']
            composer = request.form['composer']
            nrGeneratedNotes = request.form['nr_notes']

            patternFile =  STATIC_FOLDER + "\\" + patternFile
            if not os.path.isfile(patternFile):
                flash('File ' + patternFile + ' does not exist!')
                return render_template('auth/ProfessorGenerateMusic.html', form=form)

            lilyFile = STATIC_FOLDER + "\\" + os.path.basename(lilyFile).split('.')[0] + ".ly"
            pdfScoreSheet = STATIC_FOLDER + "\\" + os.path.basename(lilyFile).split('.')[0]

            # dctLetters will contain  a dictionary of frequencies of appearances for all letters that appear after
            # the key of the dictionary.
            dctLetters = buildFrequencyMatrix(patternFile)
            # First valid letter that can be used for starting Markov's chain
            firstLetter = getFirstValidChar(patternFile)
            textToNotes = firstLetter
            prevChar = firstLetter

            for cnt in range(int(nrGeneratedNotes)):
                nextChar = getNextLetter(prevChar, dctLetters)
                if not(nextChar is not None and nextChar in char2notes.keys()):
                    # If it happens to return an invalid character, just generate a random char and continue the algorithm
                    nextChar = chr(randint(97, 122)).lower()
                prevChar = nextChar
                textToNotes = textToNotes + nextChar

            title = ("\header {"
                     "title = \"Computer generated music\""
                     "composer = " + composer + " using Python"
                     "tagline = \"Copyright: " + composer + "\""
                     "}")

            # Generate the notes file in format that Lilypond can process
            (upper_staff,lower_staff) =  GenerateStaff(textToNotes)
            staff = "\score {\n"
            staff += "{\n"
            staff += "{\n\\new PianoStaff << \n"
            staff += "  \\new Staff {" + upper_staff + "}\n"
            staff += "  \\new Staff { \clef bass " + lower_staff + "}\n"
            staff += ">>\n}\n"
            staff += "}\n"
            staff += "\layout { }\n"
            staff += "\midi { }\n"
            staff += "}\n"

            file = open(lilyFile, "w")
            file.write(title + staff)
            file.close()

            cmd = "lilypond.exe -f pdf -o " + pdfScoreSheet + " " + lilyFile
            proc = subprocess.Popen(cmd, shell = True,stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            (out, err) = proc.communicate()
            if len(str(err)) > 0 and 'Changing working directory to' not in str(err):
                flash('Error: ' + str(format(err)))
            flashMsg = "Pdf score sheet: " + pdfScoreSheet + ".pdf and midi file: " + os.path.basename(lilyFile) + "/" + os.path.basename(lilyFile).split('.')[0] + ".midi have been created successfully"
            flash(flashMsg)
        except Exception as err:
            flash('Error: ' + str(format(err)))
    return render_template('auth/ProfessorGenerateMusic.html', form = form)



def GenerateStaff(phrase):
    # Define a dictionary that converts characters to notes.
    # This is needed just for the placeholder algorithm that generates music based on provided phrase.
    # Later on to be replaced by the implementation of the algorithm provided by the professor.
    char2notes = {
        ' ': ("a4 a4 ", "r2 "),
        'a': ("<c a>2 ", "<e' a'>2 "),
        'b': ("e2 ", "e'4 <e' g'> "),
        'c': ("g2 ", "d'4 e' "),
        'd': ("e2 ", "e'4 a' "),
        'e': ("<c g>2 ", "a'4 <a' c'> "),
        'f': ("a2 ", "<g' a'>4 c'' "),
        'g': ("a2 ", "<g' a'>4 a' "),
        'h': ("r4 g ", " r4 g' "),
        'i': ("<c e>2 ", "d'4 g' "),
        'j': ("a4 a ", "g'4 g' "),
        'k': ("a2 ", "<g' a'>4 g' "),
        'l': ("e4 g ", "a'4 a' "),
        'm': ("c4 e ", "a'4 g' "),
        'n': ("e4 c ", "a'4 g' "),
        'o': ("<c a g>2  ", "a'2 "),
        'p': ("a2 ", "e'4 <e' g'> "),
        'q': ("a2 ", "a'4 a' "),
        'r': ("g4 e ", "a'4 a' "),
        's': ("a2 ", "g'4 a' "),
        't': ("g2 ", "e'4 c' "),
        'u': ("<c e g>2  ", "<a' g'>2"),
        'v': ("e4 e ", "a'4 c' "),
        'w': ("e4 a ", "a'4 c' "),
        'x': ("r4 <c d> ", "g' a' "),
        'y': ("<c g>2  ", "<a' g'>2"),
        'z': ("<e a>2 ", "g'4 a' "),
        '\n': ("r1 r1 ", "r1 r1 "),
        ',': ("r2 ", "r2"),
        '.': ("<c e a>2 ", "<a c' e'>2")}

    upper_staff = ""
    lower_staff = ""
    for i in phrase.lower():
        (l, u) = char2notes[i]
        upper_staff += u
        lower_staff += l
    return (upper_staff,lower_staff)


def getNextLetter(letter, dctLetters):
    """ Based on the input letter and the dictionary of frequencies provided, returns the next most probable note to appear.
    """
    # At this stage the keys of dctLetter point to a dictionary of frequencies of the chars that appear after that letter
    dctFrequency = dctLetters[letter]
    dctSortedFreq = sorted(dctFrequency.items(), key=operator.itemgetter(1))
    # get the highest frequency for a next letter
    highestFreq = dctSortedFreq[-1][-1]
    # generate a random number between 0 and the highest frequency.
    randNumber = randint(0, highestFreq)
    if randNumber == 0:
        # return first key in the sorted list
        return dctSortedFreq[0][0]
    if randNumber == highestFreq:
        # return last key in the sorted list
        return dctSortedFreq[-1][0]

    firstLoop = False
    retKey = None
    for key in dctSortedFreq:
        # dctSortedFreq is a list. Key is a tuple containing 2 elements (the character and the frequency)
        if firstLoop == False:
            prevValue = key[1]
            crtValue = key[1]
            prevKey = key[0]
            crtKey = key[0]
            firstLoop = True
        else:
            prevValue = crtValue
            crtValue = key[1]
            prevKey = crtKey
            crtKey = key[0]

        if randNumber >= prevValue and randNumber < crtValue:
            if randNumber - prevValue < crtValue - randNumber:
                if prevKey is None:
                    print ('prevValue: ', prevValue)
                    print('prevKey: None', )
                retKey = prevKey
            else:
                if crtKey is None:
                    print('crtValue: ', crtValue)
                    print('crtKey: None', )
                retKey = crtKey

    """
    if '!' in retKey: ##
        print('Random number: ', randNumber)
        print('Highest frequency: ', highestFreq)
        print('Sorted list: ', dctSortedFreq)
        print ('Input letter: ', letter) ##
    """
    return retKey

def buildFrequencyMatrix(fileName):
    """ Based on the text provided in fileName, builds a dictionary of letters.
        The key in this dictionary is a letter and the value is a dictionary of frequencies with which the other letters appear
        Returns back the built dictionary
    """

    # loop through char2notes and analyze each letter in the context of the provided text
    with open(fileName, "r") as f:
        data = f.read()
    f.close()

    excludeSpecialCharList = ['[',']','(',')']
    dctLetters = {}
    for letter in char2notes:
        dctFrequency = {}
        for cnt in range(len(data)):
            # Calculate frequency of next characters only for the chars that are keys in the char2notes dictionary.
            crtLetter = data[cnt].lower()
            if crtLetter in excludeSpecialCharList or crtLetter not in char2notes.keys():
                continue

            if letter == crtLetter:
                nextLetter = data[cnt + 1].lower()
                if nextLetter in  dctFrequency.keys():
                    dctFrequency[nextLetter] = dctFrequency[nextLetter] + 1
                else:
                    dctFrequency[nextLetter] = 1
        dctLetters[letter] = dctFrequency

    return dctLetters

def getFirstValidChar(fileName):
    with open(fileName, "r") as f:
        data = f.read()
    f.close()

    cnt = 0
    crtLetter = None
    keysList = char2notes.keys()

    while cnt < len(data):
        crtLetter = data[cnt].lower()
        cnt = cnt + 1
        if crtLetter in keysList:
            return crtLetter

    return crtLetter