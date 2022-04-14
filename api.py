from hashlib import sha256
from flask import Flask, Response, request, render_template, flash
from wtforms import Form, TextAreaField, TextAreaField, validators
import pymongo

# App configuration
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "f79c49f8cff36434256e56b610824ea695e88b36a23317c61cfdbd8b198b642c"

# basic info

# perms:
# 0 : No permissions
# 1 : Read only
# 2 : Read and Write
# 3 : Admin (can change other users' permissions)

# MongoDB configuration
try:
    # Connection parameters
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.PokeFiles
    mongo.server_info()

# Raise exception if connection fails
except:
    print("ERROR: Connection to MongoDB failed")

# WTForms registration
class RegistrationForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Name:", validators=[validators.DataRequired()])

# WTForms login
class LoginForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms confirm email
class ValidationForm(Form):
    email = TextAreaField("Confirm your email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    validationCode = TextAreaField("Validation code:", validators=[validators.DataRequired()])

# Routes
@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
  
# Register user
def regMain():

    # Select wtform format
    form = RegistrationForms(request.form)
    print(form.errors)
    
    # Only accept POST requests
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        name = request.form["name"]

        # Validate data passed into forms
        if form.validate():
            
            # Encrypt info and store into DB.
            info = [username, password]
            encryptedInfo = []
            for i in info:
                encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest())

            # Compose dict with info
            user = {
                "username": encryptedInfo[0],
                "password": encryptedInfo[1],
                "email": email,
                "name": name,
                "perms": 0,
                }
            
            # Check for duplicity
            if db.users.find_one({"username": user['username']}):
                flash("Username taken. Try another one!")
                return render_template('/public/registration.html', form=form)

            if db.users.find_one({"email": user['email']}):
                flash("Email already registered! Enter another one.")
                return render_template("/public/registration.html", form=form)

            # Send to DB
            dbResponse = db.users.insert_one(user)
            dbResponse.inserted_id

            # Visual indication of success
            flash("Registration done. ", encryptedInfo)
            return render_template("/public/hello.html", form=form)

        # Visual indication of failure
        else:
            flash("Error! All form fields are required. ")

    # What to do if it fails
    return render_template("/public/registration.html", form=form)

def loginPage():

    # Select wtform format
    form = LoginForms(request.form)
    username = request.form("username")
    password = request.form("password")

    # Validate form requirements
    if form.validate():
        user = db.users.find_one({
            "username":username,
            "password":password
        })
        if user:
            return print("AAAAAAAAAAAAAAAHHHHHHHHHHHHHHHHHH")
        return render_template("/public/registration.html")

# Run app
if __name__ == "__main__":
    app.run()