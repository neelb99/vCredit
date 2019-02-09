from flask import Flask, render_template, request, redirect,session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime,timedelta

app = Flask(__name__)
#session key
app.secret_key = "abdhasbdjansdkansdjkansdjkasnd"

#database initializing
engine = create_engine("postgres://ibtulmwkycacxc:09dee55f0c884bc862d36edae646d0cb3c9f7d30580236979f15dec78dd4b297@ec2-54-225-121-235.compute-1.amazonaws.com:5432/d23t9c4c58u4un")
db = scoped_session(sessionmaker(bind=engine))

#home page
@app.route("/")
def index():
    if 'rollno' in session:
        if 'admin' in session:
            isadmin=True
        else:
            isadmin=False
        return render_template('index.html', logged=True, isadmin=isadmin)
    else:
        return render_template('index.html', logged=False, isadmin=False)

#register page
@app.route("/register", methods=["GET","POST"])
def register():
    if 'admin' in session:
        isadmin=True
    else:
        isadmin=False
    if request.method == "GET":
        if 'rollno' in session:
            return redirect('/account')
        else:
            return render_template('register.html', alreadyexists=False,isadmin=isadmin,logged=False)
    else:
        if 'rollno' in session:
            return redirect('/account')
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
                return redirect('/account')
            else:
                return render_template('register.html',alreadyexists=True,isadmin=isadmin,logged=False)


@app.route("/login", methods=["GET","POST"])
def login():
    if 'admin' in session:
        isadmin=True
    else:
        isadmin=False
    if request.method == "GET":
        if 'rollno' in session:
            return redirect('/account')
        else:
            return render_template('login.html',wrong=False,isadmin=isadmin,logged=False)
    else:
        if 'rollno' in session:
            return redirect('/account')
        else:
            roll = request.form.get("roll").strip()
            check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
            if not check:
                return render_template('login.html', wrong=True,isadmin=isadmin)
            else:
                password = request.form.get("pass").strip()
                if check.password == password:
                    session['rollno']=roll.upper()
                    if session['rollno']=='ADMIN':
                        session['admin']=True
                    return redirect('/account')
                else:
                    return render_template('login.html', wrong=True,isadmin=isadmin,logged=False)

@app.route("/account")
def account():
    if 'admin' in session:
        isadmin=True
    else:
        isadmin=False
    if 'rollno' in session:
        user = db.execute("SELECT * from users where roll = :rollno", {"rollno": session['rollno']}).fetchone()
        transhistory = db.execute("SELECT * from transactions where sender = :sender or receiver= :receiver order by timestamp desc;",
                                  {"sender":session['rollno'].upper(), "receiver":session['rollno'].upper()}).fetchall()
        return render_template('account.html',logged=True,getname=user.name,getroll=user.roll,getbal=user.balance, isadmin=isadmin, history=transhistory)
    else:
        return redirect('/login')

@app.route("/pay")
def pay():
    if 'admin' in session:
        isadmin=True
    else:
        isadmin=False
    if 'rollno' in session:
        return render_template('pay.html',logged=True, loggedout=False, wrong=False, insufficient=False,isadmin=isadmin)
    else:
        return render_template('pay.html',logged=False, loggedout=True, wrong=False, insufficient=False,isadmin=isadmin)

@app.route("/verify",methods=["POST","GET"])
def verify():
    if request.method=="GET":
        return redirect('/pay')
    else:
        if 'admin' in session:
            isadmin=True
        else:
            isadmin=False
        if 'rollno' in session:
            roll = session['rollno']
            logged=True
            loggedout = False
        else:
            logged=False
            loggedout=True
            roll = request.form.get("roll").strip()
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        if not check:
            return render_template('pay.html',logged=logged, loggedout=loggedout,wrong=True, insufficient=False, isadmin=isadmin)
        else:
            if 'rollno' in session:
                logged=True
                user = db.execute("SELECT * from users where roll = :rollno", {"rollno": session['rollno']}).fetchone()
                password = user.password
            else:
                logged=False
                password = request.form.get("pass").strip()
            if check.password != password:
                return render_template('pay.html',logged=logged, loggedout=loggedout, wrong=True, insufficient=False,isadmin=isadmin)
            else:
                receiver = request.form.get("receiver").strip()
                check2 = db.execute("SELECT * from users where roll = :rollno", {"rollno": receiver.upper()}).fetchone()
                if not check2:
                    return render_template('pay.html',logged=logged, loggedout=loggedout, wrong=True, insufficient=False,isadmin=isadmin)
                else:
                    amount = request.form.get("amount").strip()
                    if int(amount)>check.balance:
                        return render_template('pay.html',logged=logged, loggedout=loggedout, wrong=False, insufficient=True, isadmin=isadmin)
                    elif int(amount) == 0:
                        return render_template('pay.html', logged=logged, loggedout=loggedout, wrong=True,
                                               insufficient=False, isadmin=isadmin)
                    else:
                        db.execute("update users set balance = :newbal where roll = :rollno",{"newbal":check.balance-int(amount),"rollno": roll.upper()})
                        db.execute("update users set balance = :newbal2 where roll = :rollno", {"newbal2":check2.balance+int(amount),"rollno": receiver.upper()})
                        time = datetime.now() + timedelta(hours=5, minutes=30)
                        strtime = time.strftime("%d-%m-%Y at %H:%M")
                        db.execute("insert into transactions (sender,receiver,amount,timestamp) VALUES(:sender,:receiver,:amount,:time)",
                                   {"sender":roll.upper(), "receiver":receiver.upper(),"amount":int(amount),"time":strtime})
                        db.commit()
                        return render_template('verify.html',logged=logged,payer=check.name,receiver=check2.name, amount=amount, time=strtime, isadmin=isadmin)

@app.route("/logout")
def logout():
    if 'rollno' in session:
        session.pop('rollno',None)
        if 'admin' in session:
            session.pop('admin',None)
        return redirect('/')
    else:
        return redirect('/')

@app.route("/update")
def update():
    if 'rollno' in session:
        if 'admin' in session:
            return render_template('update.html',isadmin=True, logged=True)
        else:
            return redirect('/')
    else:
        return redirect('/')

@app.route("/updateverify",methods=["GET","POST"])
def updateverify():
    if 'rollno' in session:
        if 'admin' in session:
            password = request.form.get("pass").strip()
            admin = db.execute("Select * from users where roll='ADMIN'").fetchone()
            if password == admin.password:
                amount = request.form.get("amount").strip()
                roll = request.form.get("roll").strip()
                user =  db.execute("Select * from users where roll=:rollno",{"rollno":roll.upper()}).fetchone()
                if user and (int(amount)!=0):
                    db.execute("update users set balance=:newbal where roll=:rollno",{"rollno":roll.upper(),"newbal":user.balance+int(amount)})
                    time = datetime.now() + timedelta(hours=5, minutes=30)
                    strtime = time.strftime("%d-%m-%Y at %H:%M")
                    db.execute("insert into transactions (sender,receiver,amount,timestamp) VALUES(:sender,:receiver,:amount,:time)",
                        {"sender": "ADMIN", "receiver": roll.upper(), "amount": int(amount), "time": strtime})
                    db.commit()
                    return render_template('updateverify.html',amount=amount, receiver=user.name, time=strtime, isadmin=True, logged=True)
                else:
                    return redirect('/update')
            else:
                return redirect('/update')
        else:
            return redirect('/')
    else:
        return redirect('/')

