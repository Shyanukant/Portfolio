from flask import Flask, render_template, request, flash, redirect, session 
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail   # send mail using flsk mail for more https://pythonhosted.org/Flask-Mail/
import json
import os 


# add mySQL database 
with open('config.json', 'r') as f:   # open config.json in readind mode
    params = json.load(f)["parameter"]
local_server = True
app = Flask(__name__, template_folder='template')
# set secret key
app.secret_key = 'sublesh-roshan'
# configuring flask mail
app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_ASCII_ATTACHMENTS = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pass']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False


app.config['UPLOAD_FOLDER'] = params['upload_location'] # location of contact file
app.config['UPLOAD_FOLDER2'] = params['upload_location2'] # location of upload file
#
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

###################################### database table  #################################################

# connect with database
db = SQLAlchemy(app)
# contact form table data
class Contact(db.Model):
    Sno = db.Column (db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(250),  nullable=True)
    file = db.Column(db.String(30),  nullable=True)
    date = db.Column(db.DateTime )

# post table data
class project_post(db.Model):
    Sno = db.Column (db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=False, nullable=False)
    slug = db.Column(db.String(30), unique=True, nullable=False)
    img_file = db.Column(db.String(30), unique=True, nullable=False)
    content = db.Column(db.Text(),  nullable=False)
    date = db.Column(db.DateTime )

###################################### pages  #################################################

# check submit file is currect or not
def allowed_file(fname): 
    return '.' in fname and fname.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


###################################### ##########  #################################################
###################################### main pages  #################################################

@app.route("/")
def index():
    title = "Home"
    projects = project_post.query.filter_by().all()[0:params['no-of-project']]
    return render_template("index.html", title=title, params = params, projects = projects)


 # project post code
@app.route("/project/<string:project_slug>", methods=['GET'])  # url with variable with type
def project_route(project_slug = None):
    project = project_post.query.filter_by(slug = project_slug).first_or_404(description='There is no data with {}'.format(project_slug))  # fetch project post from database
    return render_template("project.html", params = params, project = project)

@app.route("/contact", methods= ['GET','POST'])  #post for add data in database
def Contact_view():
    title = "Contact"
    if(request.method == 'POST'):
        # add entry to the database
        Name = request.form.get('name')
        Email = request.form.get('email')
        Phone = request.form.get('phone')
        Message = request.form.get('message')
        # File = request.form.get('file')
        
        file = request.files.get('file')
        # global fname
        if file and allowed_file(file.filename):
            
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname ))
            flash('Thanks For Contacting Me, I will Get Back to You Soon. file= {}'.format(fname), 'success')
        elif file.filename== '':
            flash('Thanks For Contacting Me, I will Get Back to You Soon.', 'success')
        else:
            flash('Inavalid File, Only txt, pdf, png , jpg, jpeg, gif are Valid', 'error')

        
        entry = Contact(name = Name, email = Email, phone = Phone, message = Message, file = file.filename,  date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        
        mail.send_message('New massage from ' +Name,
                            sender = Email,
                            recipients = [params['gmail-user']],  # Recieve mail after submit contact form
                            body = Message + "\n" + Phone +"\n" + Email + "\n" + str(file)
                            
                        ) 
        
                        
        return redirect('/contact')
              
    return render_template("contact.html", title=title, params= params)

###################################### ###############  #################################################
###################################### dashboard pages  #################################################


@app.route("/edit/<string:sno>", methods = ['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            image = request.form.get('image')
            date = datetime.now()

            if sno == '0' : #if serial no is 0 then Add new post
                project = project_post(title = title, slug = slug, content = content, img_file = image, date = date)
                db.session.add(project)
                db.session.commit()

            else:
                project = project_post.query.filter_by(Sno = sno).first()
                project.title = title
                project.slug = slug
                project.content = content
                project.img_file = image
                project.date = date

                db.session.commit()
                return redirect('/edit/'+sno)
        project = project_post.query.filter_by(Sno = sno).first()
        return render_template('edit.html', params=params, project = project, sno = sno)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user']== params['admin_user']:
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER2'], secure_filename(f.filename) )) # save upload file in location with file name
            # flash('Upload Succesfully, file= {}'.format(f), 'success')
            return redirect("/dashboard")

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    # if user already login
    if 'user' in session and session['user'] == params['admin_user']:
        projects = project_post.query.all() #show all post in dashboard
        return render_template('dashboard.html', params=params, projects = projects)

    if request.method == 'POST':  #post request from user for enter in admin panel
        #REDIRECT TO ADMIN PANNEL and check username and password 
        username = request.form.get('username')
        userpass = request.form.get('userpass')

        if (username == params['admin_user'] and userpass == params['admin_password']):
            # set the session variable here
            session['user'] = username
            projects = project_post.query.all()
            return render_template('dashboard.html', params= params, projects = projects)
    # else:
    return render_template("login.html", params = params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods = ['GET', 'POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        project = project_post.query.filter_by(Sno = sno).first()
        db.session.delete(project) # delete project
        db.session.commit()
    return redirect('/dashboard')

if __name__ == "__main__":
    app.run(debug=True, port=8000)