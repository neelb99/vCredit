from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine("postgresql://postgres:1677@localhost/vcredit")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template('index.html')

