from hashlib import sha256
from flask import Flask, request, Response, render_template, flash, redirect, request, jsonify
from wtforms import Form, TextAreaField, TextAreaField, validators, FileField
import pymongo
import pathlib
import os
import pprint

# App configuration
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "f79c49f8cff36434256e56b610824ea695e88b36a23317c61cfdbd8b198b642c"

# Basic info

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

# Session
session = {}

# WTForms registration
class RegistrationForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    name = TextAreaField("Name:", validators=[validators.DataRequired()])

# WTForms login
class LoginForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms confirm email
class ValidationForm(Form):
    email = TextAreaField("Confirm your email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    validationCode = TextAreaField("Validation code:", validators=[validators.DataRequired()])

# WTForms files
class FilesForm(Form):
    files = FileField("Upload files:", validators=[validators.DataRequired()])

app.config["FILE_UPLOADS"] = str(pathlib.Path().resolve()) + "\\uploads"

# Upload files
@app.route("/upload-file", methods = ["GET", "POST"])
def upload_file():
    
    # If request method is POST
    if request.method == "POST":
        
        # Select wtforms method
        form = FilesForm(request.form)

        try:
            
            if request.files:
                
                files = request.files.getlist("file")

                for file in files:
                    file.save(os.path.join(app.config["FILE_UPLOADS"], file.filename))

                return render_template("public/uploads.html", form=form)

            else:
                
                return render_template("public/uploads.html", form=form)
        except:

            # If there's no files to upload
            return render_template("public/uploads.html", form=form)

    else:
        # If user tries to upload without being logged in
        return render_template("public/denied.html")

# Register user
@app.route("/newuser", methods = ["GET", "POST"])
def regMain():

    print(session,"SOU SESSION")

    # Select wtform format
    form = RegistrationForms(request.form)
    print(form.errors)
    
    # Only accept POST requests
    if request.method == "POST":

        print("REG IF")
        # print(session)
        # if session:
        #     flash("You already have a account! Wanna login now?")
        #     return render_template("/public/login.html", form=form)
        try:
            print("REG TRY")
            username = request.form["username"]
            password = request.form["password"]
            email = request.form["email"]
            name = request.form["name"]
            print(username, password, email, name)

            # Validate data passed into forms
            if form.validate():
                print("REG TRY IF")
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
                print(user["username"], user["password"], user["email"], user["name"], user["perms"], "AAAAAAAAAAAAAAAAAAAAAAAAAAA")
                # Check for duplicity
                if db.users.find_one({"username": user['username']}):
                    flash("Username taken. Try another one!")
                    print("QUEIJO")
                    return render_template('/public/newuser.html', form=form)

                if db.users.find_one({"email": user['email']}):
                    print("ARCARAIO")
                    flash("Email already registered! Enter another one.")
                    return render_template("/public/newuser.html", form=form)

                # Send to DB
                dbResponse = db.users.insert_one(user)
                dbResponse.inserted_id

                # Visual indication of success
                flash("Registration done. ", encryptedInfo)
                print("REQUEIJÃO")
                return render_template("/public/login.html", form=form)
            # Visual indication of failure
            else:
                print("ELSE!!!!")
                flash("Error! All form fields are required. ", form=form)
        except:
            flash("Error! Password and Email must have at least 6 characters. ", "error")
            return render_template("/public/newuser.html", form=form)

    # What to do if it fails

# First page
@app.route("/", methods = ["GET", "POST"])
def homePage():
    print("UÉ?")
    # Select wtforms format
    form = RegistrationForms(request.form)

    # And render the newuser landing page
    return render_template("/public/landing.html", form=form)


# Login user
@app.route("/login", methods = ["GET", "POST"])
def loginPage():

    # Only accept POST
    if request.method == "POST":
        # Select WTForms format
        form = LoginForms(request.form)
        print(form.errors)

        try:
            username = request.form["username"]
            password = request.form["password"]

            # Encrypt info and store into DB.
            info = [username, password]
            encryptedInfo = []
            for i in info:
                    encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest())

            # Set user
            user = {"username": encryptedInfo[0], "password": encryptedInfo[1]}

            # Find user in db
            data = db.users.find_one({"username":user["username"], "password":user["password"]})

            # Store values in session
            for key, value in data.items():
                session.update({key: value})

            # If db query returns True
            if data:

                # Visual indication of success
                flash("Logged in successfully")

                # Render user's userarea
                return render_template("/public/userarea.html", form=form)
                
        except:

            # Visual indication of failure
            flash("Login or password incorrect")
            return render_template("/public/login.html", form=form)
    
    else:
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        return render_template("/public/login.html", form=form)

# Run app
if __name__ == "__main__":
    app.run()