from hashlib import sha256
from flask import Flask, request, Response, render_template, flash, redirect, request
from wtforms import Form, TextAreaField, TextAreaField, validators
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
    name = TextAreaField("Name:", validators=[validators.DataRequired()])

# WTForms login
class LoginForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms confirm email
class ValidationForm(Form):
    email = TextAreaField("Confirm your email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    validationCode = TextAreaField("Validation code:", validators=[validators.DataRequired()])

app.config["FILE_UPLOADS"] = str(pathlib.Path().resolve()) + "\\uploads"

# Upload files
@app.route("/upload-file", methods = ["GET", "POST"])
def upload_file():

    if request.method == "POST":
        try:

            if request.files:

                files = request.files.getlist("file")

                for file in files:
                    file.save(os.path.join(app.config["FILE_UPLOADS"], file.filename))

                print("SALVO CARAI")

                return redirect(request.url)

        except:
            return render_template("public/uploads.html")

# Register user
@app.route("/newuser", methods = ["GET", "POST"])
def regMain():

    # Select wtform format
    form = RegistrationForms(request.form)
    print(form.errors)
    
    # Only accept POST requests
    if request.method == "POST":

        try:
            print("WHAT")
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
                    return render_template('/public/newuser.html', form=form)

                if db.users.find_one({"email": user['email']}):
                    flash("Email already registered! Enter another one.")
                    return render_template("/public/newuser.html", form=form)

                # Send to DB
                dbResponse = db.users.insert_one(user)
                dbResponse.inserted_id

                # Visual indication of success
                flash("Registration done. ", encryptedInfo)
                return render_template("/public/login.html", form=form)
            # Visual indication of failure
            else:
                flash("Error! All form fields are required. ")
        except:
            return render_template("/public/newuser.html", form=form)

    # What to do if it fails

# First page
@app.route("/", methods = ["GET", "POST"])
def homePage():
    form = RegistrationForms(request.form)
    return render_template("/public/newuser.html", form=form)


# Login user
@app.route("/login", methods = ["GET", "POST"])
def loginPage():

    form = LoginForms(request.form)
    print(form.errors)

    if request.method == "POST":

        try:
            username = request.form["username"]
            password = request.form["password"]
            # Encrypt info and store into DB.

            info = [username, password]
            encryptedInfo = []
            for i in info:
                    encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest())

            user = {"username": encryptedInfo[0], "password": encryptedInfo[1]}

            if db.users.find_one({"username":user["username"], "password":user["password"]}):
                print("AAAAAAAAAAAAAAAHHHHHHHHHHHHHHHHHH")
                return render_template("/public/login.html", form=form)
                
            print("JESUS CRISTO DEU CERTO\n", username, password)
            return render_template("/public/login.html", form=form)
        
        except:
            print("OPS!!!!!!!!!!!!")
            return render_template("/public/login.html", form=form)
    
    else:
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        return render_template("/public/login.html", form=form)

# Run app
if __name__ == "__main__":
    app.run()