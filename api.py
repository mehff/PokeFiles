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

app.config["FILE_UPLOADS"] = str(pathlib.Path().resolve()) + "\\uploads"

@app.route("/upload-file", methods = ["GET", "POST"])
def upload_file():

    if request.method == "POST":

        if request.files:

            image = request.files["file"]

            image.save(os.path.join(app.config["FILE_UPLOADS"], image.filename))

            print("SALVO CARAI")

            return redirect(request.url)

    return render_template("public/uploads.html")

# Run app
if __name__ == "__main__":
    app.run()