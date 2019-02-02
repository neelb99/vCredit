from flask import Flask, render_template, request, redirect
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from user import user

app = Flask(__name__)

engine = create_engine("postgresql://postgres:1677@localhost/vcredit")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        roll = request.form.get("roll")
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        password = request.form.get("pass")
        if not check:
            name = request.form.get("name")
            currentuser = user(roll.upper(), name, password)
            db.execute("insert into users (roll,name,password,balance) VALUES(:roll,:name,:pass,:balance)",
                       {"roll": currentuser.roll, "name": currentuser.name, "pass": currentuser.password,
                        "balance": currentuser.balance})
            db.commit()
            return render_template('account.html', getname=currentuser.name, getroll=currentuser.roll,
                                   getbal=currentuser.balance)
        else:
            if check.password == password:
                return render_template('account.html', getname=check.name, getroll=check.roll,
                                       getbal=check.balance)
            else:
                return render_template('login.html', wrong=True)


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template('login.html',wrong=False)
    else:
        roll = request.form.get("roll")
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        password = request.form.get("pass")
        if not check:
            return render_template('login.html', wrong=True)
        else:
            if check.password == password:
                return render_template('account.html', getname=check.name, getroll=check.roll,
                                       getbal=check.balance)
            else:
                return render_template('login.html', wrong=True)

@app.route("/account")
def account():
    return redirect('/login')

@app.route("/pay")
def pay():
    return render_template('pay.html')

@app.route("/verify",methods=["POST","GET"])
def verify():
    if request.method=="GET":
        return redirect('/pay')
    else:
        roll = request.form.get("roll")
        check = db.execute("SELECT * from users where roll = :rollno", {"rollno": roll.upper()}).fetchone()
        if not check:
            return redirect('/pay')
        else:
            password = request.form.get("pass")
            if check.password != password:
                return redirect('/pay')
            else:
                receiver = request.form.get("receiver")
                check2 = db.execute("SELECT * from users where roll = :rollno", {"rollno": receiver}).fetchone()
                if not check2:
                    return redirect('/pay')
                else:
                    amount = request.form.get("amount")
                    if int(amount)>check.balance:
                        return redirect('/pay')
                    else:
                        db.execute("update users set balance = :newbal where roll = :rollno",{"newbal":check.balance-int(amount),"rollno": roll.upper()})
                        db.execute("update users set balance = :newbal2 where roll = :rollno", {"newbal2":check2.balance+int(amount),"rollno": receiver})
                        db.commit()
                        return render_template('verify.html',payer=check.name,receiver=check2.name, amount=amount)
