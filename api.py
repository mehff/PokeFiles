from hashlib import sha256
from flask import Flask, request, render_template, flash, request, send_file, send_from_directory
from wtforms import Form, TextAreaField, TextAreaField, validators, FileField
import pymongo
import pathlib
import os

# App configuration
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "f79c49f8cff36434256e56b610824ea695e88b36a23317c61cfdbd8b198b642c"

# Basic info

# perms:
# 0 : Download only
# 1 : Download and Upload
# 2 : Download, Upload and Delete
# 3 : Download, Upload and change others' perms

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

# File pathes
pathList = []

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

# User area
@app.route("/userarea", methods=["GET", "POST"])
def userArea():
    return render_template("/userarea.html", session=session)

# Logout user
@app.route("/logout", methods=["GET", "POST"])
def logout():
    return render_template("/landing.html", session={})

# Upload files
@app.route("/upload-file", methods = ["GET", "POST"])
def upload_file():

    try:
        if session["perms"] >= 1:
        # If request method is POST
            if request.method == "POST":
                
                # Select wtforms method
                    form = FilesForm(request.form)

                    try:
                        
                        if request.files:
                            
                            files = request.files.getlist("file")

                            for file in files:
                                file.save(os.path.join(app.config["FILE_UPLOADS"], file.filename))

                            flash("Upload successful!")
                            return render_template("uploads.html", form=form, session=session)
                        else:
                            
                            return render_template("uploads.html", form=form, session=session)
                    except:
                        flash("There's nothing to upload!")
                        # If there's no files to upload
                        return render_template("uploads.html", form=form, session=session)
        else:
            return render_template("denied.html", session={})
    except:
        return render_template("denied.html", session={})

# Download page
@app.route("/downloads", methods=["GET", "POST"])
def downloads():
    try:
        if session["perms"] >= 0:
            filenames = next(os.walk(app.config["FILE_UPLOADS"]), (None, None, []))[2]

            pathList = []
            
            for i in filenames:
                pathList.append(i)
            
            return render_template("downloads.html", session=session, pathList=pathList)
    except:
        return render_template("denied.html", session={})

# Download file
@app.route("/downloads/download/<path:filename>", methods=["GET", "POST"])
def downloadfile(filename):
    try:
        if session["perms"] >= 0:
            uploads = os.path.join(app.root_path, app.config['FILE_UPLOADS'])
            return send_from_directory(uploads, filename, as_attachment=True)
        else:
            return render_template("denied.html", session={})
    except:
        return render_template("denied.html", session={})

# Remove file
@app.route("/downloads/delete/<path:deletefilename>", methods=["GET", "POST"])
def deletefile(deletefilename):
    try:
        if session["perms"] >= 2:

            uploads = os.path.join(app.root_path, app.config['FILE_UPLOADS'])
            os.remove(uploads+"/"+deletefilename)

            filenames = next(os.walk(app.config["FILE_UPLOADS"]), (None, None, []))[2]

            pathList = []

            for i in filenames:
                pathList.append(i)
                
            return render_template("downloads.html", session=session, pathList=pathList)
        else:
            return render_template("denied.html", session={}, pathList=pathList)
    except:
        return render_template("denied.html", session={}, pathList=pathList)
# Register user
@app.route("/newuser", methods = ["GET", "POST"])
def regMain():

    # Select wtform format
    form = RegistrationForms(request.form)
    
    # Only accept POST requests
    if request.method == "POST":

        # Check if request has the info needed
        try:
            username = request.form["username"]
            password = request.form["password"]
            email = request.form["email"]
            name = request.form["name"]
            
        except:
            return render_template("/newuser.html", form=form)

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
                return render_template('/newuser.html', form=form)

            if db.users.find_one({"email": user['email']}):
                flash("Email already registered! Enter another one.")
                return render_template("/newuser.html", form=form)

            # Send to DB
            dbResponse = db.users.insert_one(user)
            dbResponse.inserted_id

            # Visual indication of success
            flash("Account created! Please login now.")
            return render_template("/login.html", form=form)
            
        else:
            # Visual indication of failure
            flash("Error! Password and Email must have at least 6 characters. ")
            return render_template("/newuser.html", form=form)

# First page
@app.route("/", methods = ["GET", "POST"])
def homePage():

    # Select wtforms format
    form = RegistrationForms(request.form)

    # And render the newuser landing page
    return render_template("/landing.html", form=form)

# Login page
@app.route("/loginPage", methods = ["GET", "POST"])
def getLogin():
    form = LoginForms(request.form)
    return render_template("/login.html", form=form)

# Login user
@app.route("/login", methods = ["GET", "POST"])
def loginPage():

    # Only accept POST
    if request.method == "POST":

        # Select WTForms format
        form = LoginForms(request.form)

        # Check if form has info
        try:
            username = request.form["username"]
            password = request.form["password"]
            
        except:
            # Render page
            return render_template("/login.html", form=form)

        # Encrypt info and store into DB
        info = [username, password]
        encryptedInfo = []

        for i in info:
            encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest())

        # Set user
        user = {"username": encryptedInfo[0], "password": encryptedInfo[1]}
        
        try:

            # Find user in db
            data = db.users.find_one({"username":user["username"], "password":user["password"]})
        except:

            # Visual indication of error
            flash("User not found!")
            return render_template("/login.html", form=form)

        try:
            # Store values in session
            for key, value in data.items():
                session.update({key: value})
        except:
            flash("Please insert your username and password")
            return render_template("/login.html", form=form)
            
        # Check if session is unpopulated (first access)
        if len(session) == 0:
            return render_template("/login.html", form=form)

        else:
            # If db query returns True
            if data.items() == session.items():

                # Render user's userarea
                return render_template("/userarea.html", session=session)

            else:
                # Visual indication of failure
                flash("Login or password incorrect")

        return render_template("/login.html", form=form)

# Run app
if __name__ == "__main__":
    app.run()