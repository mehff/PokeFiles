from hashlib import sha256
from flask import Flask, Response, request, render_template, flash
from wtforms import Form, TextAreaField, TextAreaField, validators
import pymongo

# App configuration
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "f79c49f8cff36434256e56b610824ea695e88b36a23317c61cfdbd8b198b642c"

# MongoDB configuration
try:
    # Connection parameters
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.GlobalStorageDB
    mongo.server_info()

# Raise exception if connection fails
except:
    print("ERROR: Connection to MongoDB failed")

# WTForms registration
class RegistrationForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms login
class LoginForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms confirm email
class ValidationForm(Form):
    email = TextAreaField("Confirm your email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    validationCode = TextAreaField("Validation code:", validators=[validators.DataRequired()])

# Routes
@app.route("/", methods=["GET", "POST"])

def regMain():
    form = RegistrationForms(request.form)
    print(form.errors)
    
    # Only accept POST requests
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        # Validate data passed into forms
        if form.validate():
            
            # Encrypt info and store into DB.
            # @TODO Encrypt this directly.
            info = [username, password, email]
            encryptedInfo = []
            for i in info:
                encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest())

            # Visual indication of success
            flash('Registration done. ', encryptedInfo)

            # Compose dict with info
            user = {
                "username": encryptedInfo[0],
                "password": encryptedInfo[1],
                "email": encryptedInfo[2],
                "perms": 0,
                }
            
            # Send to DB
            dbResponse = db.users.insert_one(user)
            dbResponse.inserted_id
            return render_template('/public/registration.html', form=form)

        # Visual indication of failure
        else:
            flash('Error. All form fields are required. ')

    # What to do if it fails
    return render_template('/public/registration.html', form=form)

# Run app
if __name__ == "__main__":
    app.run()