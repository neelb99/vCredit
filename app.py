from flask import Flask, render_template, request, redirect,session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os
from datetime import datetime,timedelta

app = Flask(__name__)
#session key
app.secret_key = os.urandom(24)

#database initializing
engine = create_engine("postgresql://postgres:1677@localhost/vcredit")
db = scoped_session(sessionmaker(bind=engine))

#home page
@app.route("/")
def index():
    if 'rollno' in session:
        if session["admin"]:
            adminstatus=True
        else:
            adminstatus=False
        return render_template('index.html', logged=True, isadmin=adminstatus)
    else:
        return render_template('index.html', logged=False, isadmin=False)

#register page
@app.route("/register", methods=["GET","POST"])
def register():
    if 'rollno' in session:
        return redirect('/account')
    if request.method == "GET":
        return render_template('register.html', alreadyexists=False)
    else:
        roll = request.form.get("roll").strip()
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        password = request.form.get("pass").strip()
        if not check:
            name = request.form.get("name").strip()
            db.execute("insert into users (roll,name,password,balance) VALUES(:roll,:name,:pass,:balance)",
                       {"roll": roll.upper(), "name": name, "pass": password,
                        "balance": 0})
            db.commit()
            session['rollno'] = roll.upper()
            session['admin']=False
        else:
            return render_template('register.html',alreadyexists=True)


@app.route("/login", methods=["GET","POST"])
def login():
    if 'rollno' in session:
        return redirect('/account')
    if request.method == "GET":
        return render_template('login.html',wrong=False)
    else:
        roll = request.form.get("roll").strip()
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        if not check:
            return render_template('login.html', wrong=True)
        else:
            password = request.form.get("pass").strip()
            if check.password == password:
                session['rollno']=roll.upper()
                if session['rollno']=='ADMIN':
                    session['admin']=True
                else:
                    session['admin']=False
                return redirect('/account')
            else:
                return render_template('login.html', wrong=True)

@app.route("/account")
def account():
    if 'rollno' in session:
        user = db.execute("SELECT * from users where roll = :rollno", {"rollno": session['rollno']}).fetchone()
        transhistory = db.execute("SELECT * from transactions where sender = :sender or receiver= :receiver",
                                  {"sender":session['rollno'].upper(), "receiver":session['rollno'].upper()}).fetchall()
        return render_template('account.html',getname=user.name,getroll=user.roll,getbal=user.balance, isadmin=session['admin'], history=transhistory)
    else:
        return redirect('/login')

@app.route("/pay")
def pay():
    if 'rollno' in session:
        return render_template('pay.html', loggedout=False)
    else:
        return render_template('pay.html', loggedout=True)

@app.route("/verify",methods=["POST","GET"])
def verify():
    if request.method=="GET":
        return redirect('/pay')
    else:
        if 'rollno' in session:
            roll = session['rollno']
        else:
            roll = request.form.get("roll").strip()
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        if not check:
            return redirect('/pay')
        else:
            if 'rollno' in session:
                user = db.execute("SELECT * from users where roll = :rollno", {"rollno": session['rollno']}).fetchone()
                password = user.password
            else:
                password = request.form.get("pass").strip()
            if check.password != password:
                return redirect('/pay')
            else:
                receiver = request.form.get("receiver").strip()
                check2 = db.execute("SELECT * from users where roll = :rollno", {"rollno": receiver.upper()}).fetchone()
                if not check2:
                    return redirect('/pay')
                else:
                    amount = request.form.get("amount").strip()
                    if int(amount)>check.balance:
                        return redirect('/pay')
                    else:
                        db.execute("update users set balance = :newbal where roll = :rollno",{"newbal":check.balance-int(amount),"rollno": roll.upper()})
                        db.execute("update users set balance = :newbal2 where roll = :rollno", {"newbal2":check2.balance+int(amount),"rollno": receiver.upper()})
                        time = datetime.now() + timedelta(hours=5, minutes=30)
                        strtime = time.strftime("%d-%m-%Y at %I:%M %p")
                        db.execute("insert into transactions (sender,receiver,amount,timestamp) VALUES(:sender,:receiver,:amount,:time)",
                                   {"sender":roll.upper(), "receiver":receiver.upper(),"amount":int(amount),"time":strtime})
                        db.commit()
                        return render_template('verify.html',payer=check.name,receiver=check2.name, amount=amount, time=strtime)

@app.route("/logout")
def logout():
    if 'rollno' in session:
        session.pop('rollno',None)
        return redirect('/')
    else:
        return redirect('/')

@app.route("/update")
def update():
    if 'rollno' in session:
        if session['admin']:
            return render_template('update.html')
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/updateverify",methods=["GET","POST"])
def updateverify():
    if 'rollno' in session:
        if session['admin']:
            password = request.form.get("pass").strip()
            admin = db.execute("Select * from users where roll='ADMIN'").fetchone()
            if password == admin.password:
                amount = request.form.get("amount").strip()
                roll = request.form.get("roll").strip()
                user =  db.execute("Select * from users where roll=:rollno",{"rollno":roll.upper()}).fetchone()
                if user:
                    db.execute("update users set balance=:newbal where roll=:rollno",{"rollno":roll.upper(),"newbal":user.balance+int(amount)})
                    time = datetime.now() + timedelta(hours=5, minutes=30)
                    strtime = time.strftime("%d-%m-%Y at %I:%M %p")
                    db.execute("insert into transactions (sender,receiver,amount,timestamp) VALUES(:sender,:receiver,:amount,:time)",
                        {"sender": "ADMIN", "receiver": roll.upper(), "amount": int(amount), "time": strtime})
                    db.commit()
                    return render_template('updateverify.html',amount=amount, receiver=user.name, time=strtime)
                else:
                    return redirect('/update')
            else:
                return redirect('/update')
        else:
            return redirect('/')
    else:
        return redirect('/')