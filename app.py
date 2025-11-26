from flask import Flask, render_template, request, redirect_url, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
import hashlib, json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hmsdata.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class departments(db.Model):
    __tablename__ = 'dept'
    id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(100))
    doctors = db.relationship("user", back_populates="department")

class user(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(25), nullable=False)
    role = db.Column(db.Integer, nullable=False) # Admin = 0, Patient = 1, Doctor = 2
    dept_id = db.Column(db.Integer, db.ForeignKey('dept.id'), nullable=True) # dept_id is nullable for patients/admins
    timestmp = db.Column(db.DateTime, default=datetime.utcnow)
    
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


if __name__ == '__main__':
    
    with app.app_context():
        db.create_all()
        #Checking for admin user
        adminalive=user.query.filter_by(username="admin").first()

        if not adminalive:
                passme=hashlib.md5("Change@l0gin".encode())
                admin_rec=user(username="admin",password=passme.hexdigest(),email="test@email.tld",role=0)
                db.session.add(admin_rec)
                db.session.commit()
    
    app.run(debug=True)