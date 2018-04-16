import sys,os,datetime, time
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
    StudentHomeworkRowForm, StudentHomeworkGridForm, AddHomeworkForm, ExtendDateForm, ChoseMusicSheetNameForm
from sqlalchemy import text

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
    form = LoginForm()
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
    ##form = DirectorRegistrationForm()
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
          return "File is already loaded. Changed update time."

      sql = ("insert into web.upload_files (file_name, file_location, director_id, file_upd_time, hw_id) values('" + filename + "','" + R_STATIC_FOLDER + "'," + str(g_director_id) + ",'" + file_upd_time + "'," + str(hw_id) + ")")
      db.engine.execute(sql)
      return 'file uploaded successfully'

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
         return "Current time is past deadline: " +  str(hw_deadline) + ". Homework cannot be uploaded."

      f = request.files['file']
      filename = secure_filename(f.filename)
      STATIC_FOLDER = os.path.abspath("../" + "/static")
      R_STATIC_FOLDER = STATIC_FOLDER.replace('\\', '\\\\')
      f.save(os.path.join(STATIC_FOLDER, filename))
      sql = text("select id,reviewed from web.student_files where file_name = '" + str(filename) + "' and file_location = '" + R_STATIC_FOLDER + "' and student_id = " + str(g_student_id) + " and director_id = " +str(g_professor_id))
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
              return " File has been reviewed. Cannot upload another version."
      else:
          sql = text('insert into web.student_files (file_name,file_location,student_id,hw_id,director_id) values(\'' + filename + '\',\'' + R_STATIC_FOLDER + '\',' + str(g_student_id) + ',' + str(hw_id) + ',' +str(g_professor_id) + ')')
          result = db.engine.execute(sql)
      return 'file uploaded successfully'

@auth.route("/AddStudent", methods=['GET', 'POST'])
def AddStudent():
    """ Function to add a student to a class. The professor adds a student to his/her class. """
    form = AddStudentToClassForm()
    student_list = []
    ##student_id_dict = {}
    if request.method == 'POST' and form.validate_on_submit():
        sql = ("select id, first_name, last_name "
                   "from web.student ")
        result = db.engine.execute(sql)
        for row in result:
            student_list.append(row[0])
           ## student_id_dict[row[0]] = row[1]

        email = form.data['email'].strip()
        if len(form.data['email'].strip()) > 0:
            sql = ("select id, first_name, last_name "
                   "from web.student "
                   "where email = '" + str(email)) + "'"
            result = db.engine.execute(sql)
            if result is not None:
                if result.rowcount == 0:
                    return render_template('auth/addstudentnoregisteredusers.html',email = email)
                    ##return "There are no registered users having email: " + email
                elif result.rowcount > 1:
                    return "There are multiple registered users having email: " + email
                for row in result:
                    student_id = row[0]
                    first_name = row[1]
                    last_name = row[2]
        else:
            first_name = form.data['first_name'].strip()
            last_name = form.data['last_name'].strip()
            if (len(first_name) > 0) and (len(last_name) > 0):
                sql = ("select id, email "
                       "from web.student "
                       "where first_name = '" + str(first_name)) + "' and last_name = '" + str(last_name) +"'"
                result = db.engine.execute(sql)
                if result is not None:
                    if result.rowcount == 1:
                        for row in result:
                            student_id = row[0]
                            email = row[1]
                    else:
                        if result.rowcount == 0:
                            return "There are no registered users having first name: " + str(first_name) + " and last name: " +  str(last_name)
                        return "There are more than one registered users having first name: " + str(first_name) + " and last name: " + str(last_name)
        # If we got here we have a student_id
        sql = text('select id from web.director_student where director_id = ' + str(g_director_id) + ' and student_id = ' + str(student_id))
        result = db.engine.execute(sql)
        if result.rowcount == 0:
            sql = text('insert into web.director_student (director_id,student_id) values(' + str(g_director_id) + ',' + str(student_id) + ')')
            result = db.engine.execute(sql)
            ## ADd here flash message for successfull added student.
        else:
            return "Student: " + first_name + " " + last_name + " is already added to class."
        return redirect(url_for('auth.AddStudent'))
    return render_template('auth/AddStudent.html', form=form,student_list=student_list)

# Inserts student files in the database. Called from UploadStudentFiles.html
@auth.route('/AssignFile', methods = ['GET', 'POST'])
def AssignFile():
    if request.method == 'POST':
        selected_file_id = file_id_dict[request.form['file']]
        selected_student_id = student_id_dict[request.form['student']]
        sql = ("select count(*) from web.dir_student_files where director_id = " + str(g_director_id) + " and student_id = " + str(selected_student_id) + " and file_id = " +str(selected_file_id))
        result = db.engine.execute(sql)
        for row in result:
            if row[0] > 0:
                return "File has already been assigned to this student."

        # we can safely insert now as we verified earlier that the record doesn't exist.
        sql = ("insert into web.dir_student_files (director_id,student_id,file_id) values(" + str(g_director_id) + "," +str(selected_student_id) + "," + str(selected_file_id) + ")")
        result = db.engine.execute(sql)
    return "File assigned successfully"

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
    pass # place holder
    return render_template('auth/PracticeMusic.html')

# To be deployed later
@auth.route("/UploadNewRecording", methods=['GET', 'POST'])
def UploadNewRecording():
    pass # place holder
    return render_template('auth/UploadNewRecording.html')

# To be deployed later
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

@auth.route("/ProfessorReviewFiles", methods=['GET', 'POST'])
def ProfessorReviewFiles():
    """ Function to allow professor to review files uploaded by students. """
    submitForm = ReqForm()
    teamform = GridForm()
    teamform.title.data = g_director_name

    sql = ("select sf.id, sf.file_name, CONCAT(st.first_name, ' ', st.last_name), sf.reviewed, sf.grade,sf.notes "
        "from web.student_files sf "
        "join web.student st on sf.student_id = st.id "
        "join web.director_student ds on sf.student_id = ds.student_id "
        "where ds.director_id = " + str(g_director_id) + " and sf.director_id = " + str(g_director_id) + " order by sf.reviewed DESC")
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

        file_list.append(member[1])
        teamform.grid.append_entry(member_form)

    if request.method == 'POST':
        selected_file = request.form['file']
        if request.form['btn'] == 'Review file':
            sql = ("update web.student_files set reviewed = 0, updated = NOW() where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)
            STATIC_FOLDER = os.path.abspath("../" + "/static")
            return send_from_directory(directory=STATIC_FOLDER, filename=selected_file)
        ##if request.form['btn'] == 'Mark reviewed':
        ##    sql = ("update web.student_files set reviewed = 0, updated = NOW() where file_name = '" + selected_file + "'")
        ##    result = db.engine.execute(sql)
        if request.form['btn'] == 'Grade':
            if request.form['grade'] is None or len(request.form['grade']) == 0:
               return "Grade has to be between 0 and 100"
            sql = ("update web.student_files set grade = " + str(request.form['grade']) + ", time_graded = NOW() where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)
            if request.form['notes'] is not None:
                sql = ("update web.student_files set notes = '" + str(request.form['notes']) + "' where file_name = '" + selected_file + "'")
            result = db.engine.execute(sql)

        return redirect(url_for('auth.ProfessorReviewFiles'))
    return render_template('auth/ProfessorReviewFiles.html', teamform = teamform, submitForm = submitForm,file_list = file_list)

@auth.route("/SearchStudents", methods=['GET', 'POST'])
def SearchStudents():
    """ List students assigned to a class/professor. """
    search_student_form = SearchStudentsGridForm()
    search_student_form.title.data = str(g_director_name)

    sql =   ("select st.first_name, st.last_name, st.email "
        "from web.student st "
        "   join web.director_student ds on st.id = ds.student_id "
        "where ds.director_id = " +str(g_director_id))
    result = db.engine.execute(sql)
    for member in result:
        member_form = SearchStudentsRowForm()
        member_form.first_name = member[0]
        member_form.last_name = member[1]
        member_form.email = member[2]
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
    ##sql =   ("select CONCAT(first_name, ' ', last_name) from web.director where id = " +str(g_professor_id))
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

@auth.route("/Homework", methods=['GET', 'POST'])
def Homework():
    global g_hw_name
    hw_dict = {}
    sql = ("select hw_name,hw_deadline from web.homeworks where director_id = " + str(g_director_id))
    result = db.engine.execute(sql)
    for row in result:
        hw_dict[row[0]] = row[1]
    if request.method == 'POST':
        if request.form['btn'] == 'Add homework':
            return redirect(request.args.get('next') or url_for('auth.ProfessorAddHomework'))
        if request.form['btn'] == 'Extend due date':
            g_hw_name = request.form['homework']
            return redirect(request.args.get('next') or url_for('auth.ExtendHomeworkDueDate'))

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

@auth.route("/GenerateMusic", methods=['GET', 'POST'])
def GenerateMusic():
    """ This section starts from a phrase and generates music using LilyPond and converts it into
        a PDF file that will be stored in the standard static location.
    """

    form = ChoseMusicSheetNameForm()
    if request.method == 'POST':
        file_name = request.form['file_name']

        txt = "Love one another and you will be happy. It is as simple as that."

        (upper_staff, lower_staff) = GenerateStaff(txt)
        staff = "{\n\\new PianoStaff << \n"
        staff += "  \\new Staff {" + upper_staff + "}\n"
        staff += "  \\new Staff { \clef bass " + lower_staff + "}\n"
        staff += ">>\n}\n"

        title = """\header {
          title = "Computer generated music"
          composer = "Liana Lintes using Python"
          tagline = "Copyright: Liana Lintes"
        }"""

        srcFile = STATIC_FOLDER + "\\" + file_name + ".ly"
        genFile = STATIC_FOLDER + "\\" + file_name

        file = open(srcFile, "w")
        file.write(title + staff)
        file.close()

        cmd = "lilypond.exe -f pdf -o " + genFile + " " + srcFile
        os.system(cmd)

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
