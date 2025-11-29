from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from flask import  render_template, request, url_for, session, redirect, flash

import hashlib, json

app = Flask(__name__)
app.secret_key = 'thequickbrownfoxjumpedoverthelazydog'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hmsdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class departments(db.Model):
    __tablename__ = 'dept'
    id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(100))
    deleted= db.Column(db.Boolean, default=False)

    doctors = db.relationship("user", back_populates="department")

class user(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(35), nullable=False)
    role = db.Column(db.Integer, nullable=False) # Admin = 0, Patient = 1, Doctor = 2
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=True) # dept_id is nullable for patients/admins
    blocked = db.Column(db.Boolean, default=False)
    timestmp = db.Column(db.DateTime, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    
    department = db.relationship("departments", back_populates="doctors")

class appointments(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    doc_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Integer, default=0) # 0 - Booked / 1 - Completed / 2 - Cancelled
    desc = db.Column(db.String(256), nullable=False)
    timestmp = db.Column(db.DateTime, default=datetime.utcnow)

class treatments(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    ap_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    doc_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    diag = db.Column(db.String(512), nullable=False)
    prescription = db.Column(db.String(512), nullable=False)
    notes = db.Column(db.String(512))
    timestmp = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')
    #return render_template('index.html')

@app.route('/patientdashboard')
def pdashb():
     dept=departments.query.all()
     return render_template('patient_dash.html',dept=dept)

@app.route('/doctordashboard')
def docdash():
     return render_template('doc_dash.html')

@app.route('/signup', methods=["POST","GET"])
def signup():
     error=None
     if request.method =="POST":
            name=request.form['username']
            email=request.form['email']
            password=request.form['passwd']
            password=hashlib.md5(password.encode())
            password=password.hexdigest()
            tmpuser = user.query.filter_by(email=email).first()
            if (tmpuser):
                 error="User already exists"
            else:
                registeruser=user(username=name,email=email,password=password,role=1,deleted=False)
                db.session.add(registeruser)
                db.session.commit()
                return render_template('login.html',error="Registration Successful")
                 

     return render_template('signup.html',error=error)

@app.route('/logout')
def logout():
     session.clear()
     return redirect(url_for('login')) 

@app.route('/admin-dashboard')
def admindash():
     pats=user.query.filter_by(role=1).all() 
     docts=user.query.filter_by(role=2).all()
     depts=departments.query.all()
     
     return render_template('admin_dash.html', pats=pats, docts=docts, depts=depts)

@app.route('/login',methods=["POST","GET"])
def login():
     error=None
     if request.method=="POST":
            useremail=request.form['uemail']
            password=request.form['passwd']
            password=hashlib.md5(password.encode())
            password=password.hexdigest()
            tmpuser=user.query.filter_by(email=useremail).first()
            
            if (tmpuser):
                if (tmpuser.blocked):
                    return render_template('accountblocked.html')
                if tmpuser.password==password:
                    session['name']=tmpuser.username
                    session['email']=tmpuser.email
                    session['id']=tmpuser.id
                    session['role']=tmpuser.role
                    match tmpuser.role:
                        case 0:
                            return redirect(url_for('admindash'))
                        case 1:
                            return redirect(url_for('pdashb'))
                        case 2:
                            return redirect(url_for('docdash'))
                else:
                    print("Password mismatch")
                    return render_template('login.html',error="Invalid Credentials, try again.")
            else:
                    return render_template('login.html',error="Invalid Credentials, try again.")

     return render_template('login.html')

@app.route('/bookapt')
def bookapt():
     return render_template('/patient_dash.html')

@app.route('/showhistory')
def showhistory():
     return render_template('/patient_dash.html')

@app.route('/admin-dashboard/adddoc', methods=['POST','GET'])
def adddoc():
     error=None
     dname= departments.query.all()
     if request.method =="POST":
            name=request.form['username'].title()
            email=(request.form['email']).lower()
            password=request.form['passwd']
            password=hashlib.md5(password.encode())
            password=password.hexdigest()
            dept=request.form['dept']
            tmpuser = user.query.filter_by(email=email).first()
            if (tmpuser):
                 return render_template('add_doc.html',error="Doctor already exists",dname=dname)
            else:
                registeruser=user(username=name,email=email,password=password,role=2,dept_id=dept)
                db.session.add(registeruser)
                db.session.commit()
                return render_template('add_doc.html',error="New Doctor added")
     return render_template('add_doc.html',dname=dname,)


@app.route('/admin-dashboard/editdoc', methods=['POST','GET'])
def editdoc():
     error=None
     if request.method =="POST":
            name=request.form['username']
            email=request.form['email']
            password=request.form['passwd']
            password=hashlib.md5(password.encode())
            password=password.hexdigest()
            dept=request.form['dept']
            tmpuser = user.query.filter_by(email=email).first()
            if (tmpuser):
                 error="Doctor already exists"
                 print("Doctor not added")
            else:
                registeruser=user(username=name,email=email,password=password,role=2,dept_id=dept)
                db.session.add(registeruser)
                db.session.commit()
                return render_template('add_doc.html',error="New Doctor added")
     return render_template('add_doc.html',dname=dname,error="Doctor already exists!")

@app.route('/admin-dashboard/add_dept', methods=['POST','GET'])
def add_dept():
     error=None
     dname= departments.query.all()
     if request.method =="POST":
            deptname=request.form['deptname'].title()
            desc=request.form['desc']
            tmpval = departments.query.filter_by(dept_name=deptname).first()
            if (tmpval):
                 return render_template('add_dept.html',error="Department already exists")
            else:
                newdept=departments(dept_name=deptname,description=desc)
                db.session.add(newdept)
                db.session.commit()
                return render_template('add_dept.html',error="New Department added")
     return render_template('add_dept.html')

@app.route('/admin-dashboard/view_dept/<int:dept_id>')
def view_dept(dept_id):
     error=None
     d_details=departments.query.filter_by(id=dept_id).first()
     doclist=user.query.filter_by(dept_id=dept_id)
     if (doclist.count()==0):
        doclist=None
     return render_template('view_dept.html',depts=d_details,doclist=doclist)

@app.route('/admin-dashboard/view_docs/<doc_id>')
def view_docs(doc_id):
     error=None
     doc_details=user.query.filter_by(email=doc_id).first()
     dept=departments.query.filter_by(id=doc_details.dept_id).first()
     apts=appointments.query.filter_by(doc_id=doc_details.id)
     if (apts.count()==0):
          apts=None
     print(apts)

     return render_template('view_docs.html',docdet=doc_details,dept=dept,apts=apts)
 

if __name__ == '__main__':
    
    with app.app_context():
        db.create_all()
        #Checking for admin user
        adminalive=user.query.filter_by(username="admin").first()

        if not adminalive:
                passme=hashlib.md5("Change@l0gin".encode())
                admin_rec=user(username="admin",password=passme.hexdigest(),email="admin@hms.sys",role=0,deleted=False)
                db.session.add(admin_rec)
                db.session.commit()
    
    app.run(debug=True)