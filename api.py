from hashlib import sha256
from flask import Flask, request, render_template, flash, request, send_from_directory, Markup, session
from wtforms import Form, TextAreaField, TextAreaField, validators, FileField
import pymongo
import pathlib
import os
from pyngrok import ngrok
from bson import ObjectId

# App configuration
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)

# Needs to be set to use WTForms
app.config["SECRET_KEY"] = "f79c49f8cff36434256e56b610824ea695e88b36a23317c61cfdbd8b198b642c"

# Basic info

# perms:
# 0 : Download only
# 1 : Download and Upload
# 2 : Download, Upload and Delete
# 3 : Download, Upload and change others' perms
# 4 : All the above, plus #3 can't change it's perms

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

# Setup
pathList = []
ngrokStat = 0

# WTForms newUser
class newUserForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    email = TextAreaField("Email:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])
    name = TextAreaField("Name:", validators=[validators.DataRequired()])

# WTForms login
class LoginForms(Form):
    username = TextAreaField("Username:", validators=[validators.DataRequired()])
    password = TextAreaField("Password:", validators=[validators.DataRequired(), validators.Length(min=6, max=35)])

# WTForms files
class FilesForm(Form):
    files = FileField("Upload files:")
    filesShared = FileField("Upload shared files:")

# WTForms files
class LendToForm(Form):
    lendTo = TextAreaField("Lend to:", validators=[validators.DataRequired()])

app.config["FILE_UPLOADS"] = str(pathlib.Path().resolve()) + "\\uploads"
app.config["PATHLIST"] = []
app.config["SHARED_PATHLIST"] = []


# First page
@app.route("/", methods = ["GET", "POST"])
def homePage():

    # Select wtforms format
    form = newUserForms(request.form)

    # And render the newUser landing page
    return render_template("/landing.html", form=form)

# Register user
@app.route("/newUser", methods = ["GET", "POST"])
def regMain():

    # Select wtform format
    form = newUserForms(request.form)
    
    # Only accept POST requests
    if request.method == "POST":

        # Check if request has the data needed
        try:
            username = request.form["username"]
            password = request.form["password"]
            email = request.form["email"]
            name = request.form["name"]
            
            # Verify if password is unique in the request
            if username == password or email == password or name == password:
                flash("You cannot use other provided info as password!")
                return render_template("/newUser.html", form=form)

            # Verify if password respects some rules
            if any(i.isdigit() for i in password) == False:
                flash("Your password has to have at least one number!")
                return render_template("/newUser.html", form=form)

        # Return to newUser page if it doesn't
        except:
            return render_template("/newUser.html", form=form)

        # Validate data passed into forms
        if form.validate():

            # Encrypt info and store into DB.
            info = [username, password]
            encryptedInfo = []
            for i in info:
                encryptedInfo.append(sha256(str(i).encode("utf-8")).hexdigest())

            # Compose dict with info
            user = {
                "username": encryptedInfo[0],
                "password": encryptedInfo[1],
                "email": email,
                "name": name,
                "perms": 0,
                "userFolder": encryptedInfo[0],
                "folderBorrowing": [],
                "folderLended": []
                }
                
            # Check for duplicity
            if db.users.find_one({"username": user["username"]}):
                flash("Username taken. Try another one!")
                return render_template("/newUser.html", form=form)

            if db.users.find_one({"email": user["email"]}):
                flash("Email already registered! Enter another one.")
                return render_template("/newUser.html", form=form)

            # Send to DB
            dbResponse = db.users.insert_one(user)
            dbResponse.inserted_id

            # Visual indication of success
            flash("Account created! Please login now.")
            return render_template("/login.html", form=form)
            
        else:
            # Visual indication of failure
            flash("Error! Password and Email must have at least 6 characters. ")
            return render_template("/newUser.html", form=form)

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
            encryptedInfo.append(sha256(str(i).encode("utf-8")).hexdigest())

        # Set user
        user = {"username": encryptedInfo[0], "password": encryptedInfo[1]}
        
        try:

            # Find matching user and password in db
            data = db.users.find_one({"username":user["username"], "password":user["password"]})
        except:

            # Visual indication of error
            flash("User not found!")
            return render_template("/login.html", form=form)

        # Store values in session
        try:
            for key, value in data.items():
                if type(value) == ObjectId:
                    session.update({key: str(value)})
                elif key == "password":
                    pass
                elif key == "userFolder":
                    app.config["USER_FOLDER"] = app.config["FILE_UPLOADS"] + "\\" + value
                elif key == "folderBorrowing":
                    session.update({key: value})
                    app.config["FOLDER_BORROWING"] = value
                elif key == "folderLended":
                    session.update({key: value})
                    app.config["FOLDER_LENDED"] = value
                else:
                    session.update({key: value})
            
            # Create personal user folder
            userFolder = app.config["USER_FOLDER"]
            
            if not os.path.exists(userFolder):
                os.makedirs(userFolder)
                
        except:
            flash("Please insert your username and password")
            return render_template("/login.html", form=form)

        # Check if session is unpopulated (first access)
        if len(session) == 0:
            return render_template("/login.html", form=form)

        else:
            # If db query returns True
            if len(session.items()) != 0:

                # Render user's userarea
                return render_template("/userarea.html", ngrokStat=ngrokStat, form=form)

            else:
                # Visual indication of failure
                flash("Login or password incorrect")

        return render_template("/login.html", form=form)

# User area
@app.route("/userarea", methods=["GET", "POST"])
def userArea():
    # try:
        if session["perms"] >= 0:
            
            print(app.config["USER_FOLDER"])

            userFolder = app.config["USER_FOLDER"]
            
            # Check if user folder is there
            if not os.path.exists(userFolder):
                os.makedirs(userFolder)

            return render_template("/userarea.html", ngrokStat=ngrokStat)
    # except:
    #     return render_template("denied.html", )

# Logout user
@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return render_template("/landing.html")

# Download page
@app.route("/downloads", methods=["GET", "POST"])
def downloads():
    # try:
        if session["perms"] >= 0:

            # Get local uploads folder content and save to pathList
            filenames = next(os.walk(app.config["USER_FOLDER"]), (None, None, []))[2]
            
            app.config["PATHLIST"].clear()

            pathList = []
            
            for i in filenames:
                pathList.append(i)
                app.config["PATHLIST"].append(i)

            sharedFilenames = next(os.walk(app.config["FILE_UPLOADS"] + "\shared"), (None, None, []))[2]

            app.config["SHARED_PATHLIST"].clear()

            sharedPathList = []

            for i in sharedFilenames:
                sharedPathList.append(i)
                app.config["SHARED_PATHLIST"].append(i)

            print(app.config["SHARED_PATHLIST"])
            print(app.config["PATHLIST"])

        return render_template("downloads.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])

    # except:
    #     return render_template("denied.html")

# Download user folder file
@app.route("/downloads/download/<path:filename>", methods=["GET", "POST"])
def downloadfile(filename):
    try:
        if session["perms"] >= 0:

            # Return the right file
            uploads = os.path.join(app.root_path, app.config["USER_FOLDER"])
            return send_from_directory(uploads, filename, as_attachment=True)
        else:
            return render_template("denied.html")
    except:
        return render_template("denied.html")

# Download user folder file
@app.route("/downloads/downloadShared/<path:filename>", methods=["GET", "POST"])
def downloadShared(filename):
    try:
        if session["perms"] >= 0:

            # Return the right file
            uploads = os.path.join(app.root_path, app.config["FILE_UPLOADS"] + "\shared")
            return send_from_directory(uploads, filename, as_attachment=True)
        else:
            return render_template("denied.html")
    except:
        return render_template("denied.html")
        
# Remove file
@app.route("/downloads/delete/<path:deletefilename>", methods=["GET", "POST"])
def deletefile(deletefilename):
    try:
        if session["perms"] >= 2:

            # Remove the right file
            uploads = os.path.join(app.root_path, app.config["USER_FOLDER"])
            os.remove(uploads+"/"+deletefilename)

            filenames = next(os.walk(app.config["USER_FOLDER"]), (None, None, []))[2]

            app.config["PATHLIST"].clear()

            pathList = []

            for i in filenames:
                pathList.append(i)
                app.config["PATHLIST"].append(i)

            return render_template("downloads.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])
        else:
            return render_template("denied.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])
    except:
        return render_template("denied.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])

# Remove shared file
@app.route("/downloads/deleteShared/<path:deletefilename>", methods=["GET", "POST"])
def deleteShared(deletefilename):
    try:
        if session["perms"] >= 2:

            # Remove the right file
            uploads = os.path.join(app.root_path, app.config["FILE_UPLOADS"] + "\shared")
            os.remove(uploads+"/"+deletefilename)

            filenames = next(os.walk(app.config["FILE_UPLOADS"] + "\shared"), (None, None, []))[2]

            app.config["SHARED_PATHLIST"].clear()

            sharedPathList = []

            for i in filenames:
                sharedPathList.append(i)
                app.config["SHARED_PATHLIST"].append(i)
                
            return render_template("downloads.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])
        else:
            return render_template("denied.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])
    except:
        return render_template("denied.html", pathList=app.config["PATHLIST"], sharedPathList=app.config["SHARED_PATHLIST"])

# Verify existing files
def checkExisting(fileName, fileExt, loopCount):

    # Check if file isn't there and if loopCount equals zero
    # Returns unaltered file name
    if os.path.exists((os.path.join(app.config["USER_FOLDER"], fileName + fileExt))) == False and loopCount == 0:
        loopCount = loopCount + 1
        return fileName + fileExt

    # If the file exists:
    # Returns itself
    elif os.path.exists((os.path.join(app.config["USER_FOLDER"], fileName + "_" + str(loopCount) + fileExt))):
        loopCount = loopCount + 1
        return checkExisting(fileName, fileExt, loopCount)

    # Returns altered name for each file that respects the conditions
    else:
        return fileName + "_" + str(loopCount) + fileExt

# Verify existing files on Shared
def checkExistingShared(fileName, fileExt, loopCount):

    # Check if file isn't there and if loopCount equals zero
    # Returns unaltered file name
    if os.path.exists((os.path.join(app.config["FILE_UPLOADS"] + "\shared", fileName + fileExt))) == False and loopCount == 0:
        loopCount = loopCount + 1
        return fileName + fileExt

    # If the file exists:
    # Returns itself
    elif os.path.exists((os.path.join(app.config["FILE_UPLOADS"] + "\shared", fileName + "_" + str(loopCount) + fileExt))):
        loopCount = loopCount + 1
        return checkExisting(fileName, fileExt, loopCount)

    # Returns altered name for each file that respects the conditions
    else:
        return fileName + "_" + str(loopCount) + fileExt

# Upload files
@app.route("/upload-file", methods = ["GET", "POST"])
def upload_file():

    try:
        if session["perms"] >= 1:

        # If request method is POST
            if request.method == "POST":
                
                # Select wtforms method
                form = FilesForm(request.form)

                # If there's files
                if request.files:
                    
                    # User feedback
                    currUploads = []

                    # Get files
                    files = request.files.getlist("file")
                    for file in files:

                        fileName, fileExt = os.path.splitext(file.filename)

                        # Check if button is pressed without selecting files
                        if fileName == "" or fileExt == "":
                            flash("There's nothing to upload!")
                            return render_template("uploads.html", form=form)

                        # If there's files
                        else:
                            uniqueFile = checkExisting(fileName, fileExt, 0)
                            file.save(os.path.join(app.config["USER_FOLDER"], uniqueFile))
                            currUploads.append(uniqueFile)
                    flash(f"The following files were uploaded: {currUploads}")
                    return render_template("uploads.html", form=form)
                else:
                    flash("There's nothing to upload!")
                    # If there's no files
                    return render_template("uploads.html", form=form)
    except:
        return render_template("denied.html")

# Upload files
@app.route("/upload-Shared", methods = ["GET", "POST"])
def upload_Shared():

    # try:
        if session["perms"] >= 1:

        # If request method is POST
            if request.method == "POST":
                
                # Select wtforms method
                form = FilesForm(request.form)

                # If there's files
                if request.files:
                    
                    # User feedback
                    currUploads = []

                    # Get files
                    files = request.files.getlist("file")
                    for file in files:

                        fileName, fileExt = os.path.splitext(file.filename)

                        # Check if button is pressed without selecting files
                        if fileName == "" or fileExt == "":
                            flash("There's nothing to upload!")
                            return render_template("uploads.html", form=form)

                        # If there's files
                        else:
                            uniqueFile = checkExistingShared(fileName, fileExt, 0)
                            file.save(os.path.join(app.config["FILE_UPLOADS"] + "\shared", uniqueFile))
                            currUploads.append(uniqueFile)
                    flash(f"The following files were uploaded to Shared: {currUploads}")
                    return render_template("uploads.html", form=form)
                else:
                    flash("There's nothing to upload!")
                    # If there's no files
                    return render_template("uploads.html", form=form)
    # except:
    #     return render_template("denied.html")

# # # TODO: Borrowing and Lending
# # Lend to user
# @app.route("/lendToUser", methods=["GET", "POST"])
# def lendToUser():
#     try:
#         if session["perms"] >= 1:

#             form = LendToForm(request.form)

#             borrowingName = []

#             for i in session["folderBorrowing"]:
#                 data = db.users.find_one({"username": i})
#                 if data:
#                     for k, v in data.items():
#                         if k == "name":
#                             print
#                             borrowingName.append(v)
#                             return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], borrowingName=borrowingName, folderLended=session["folderLended"], form = form)
#                         else:
#                             pass
#                 else:
#                     return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], borrowingName=borrowingName, folderLended=session["folderLended"], form = form)

#             if form.validate():

#                 emailToLend = request.form["lendTo"]
                
#                 folderLender = []
#                 lenderName = []

#                 data = db.users.find_one({"email": emailToLend})

#                 if data:
#                     for k, v in data.items():
#                         if k == "userFolder":
#                             folderLender = v
#                         if k == "folderBorrowing":
#                             db.users.update_one({"username": folderLender}, {"$push": {"folderBorrowing":{session["username"]: session["username"]}}})
#                             session["folderBorrowing"].append(folderLender)
#                         if k == "email":
#                             lenderName = v
#                         else:
#                             pass
                
#                 else:
#                     return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], borrowingName=borrowingName, folderLended=session["folderLended"], form = form)

#                 data = db.users.update_one({"username": session["username"]}, {"$push": {"folderLended":{folderLender: folderLender}}})

#                 return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], borrowingName=borrowingName, folderLended=session["folderLended"], lenderName=lenderName, form = form)


#             else:
#                 return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], borrowingName=borrowingName, folderLended=session["folderLended"], form = form)

#     except:
#         return render_template("denied.html")

# # Stop borrowing
# @app.route("/stopBorrowing/<path:userToStopBorrowing>", methods=["GET", "POST"])
# def stopBorrowing(userToStopBorrowing):
#     try:
#         if session["perms"] >= 2:
#             data = db.users.find_one({"username": userToStopBorrowing})
#             if data:
#                 for k, v in data.items():
#                     if k == "folderLended":
#                         j = len(v)
#                         while j > 0:
#                             if (v[j-1]) == session["username"]:
#                                 # db.users.update_one({"username": userToStopBorrowing}, {"$push": {"folderLended":{v[j-1]: v[j-1]}}})
#                                 db.users.update_one({"username": userToStopBorrowing}, {"$pull": {"folderLended":{v[j-1]}}})
#                                 j-=1
#                             else:
#                                 j-=1
#                     else:
#                         pass
#             else:
#                 return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], folderLended=session["folderLended"])
#             return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], folderLended=session["folderLended"])

#     except:
#         return render_template("denied.html")

# # Stop lending:
# @app.route("/stopLending/<path:userToStopLending>")
# def stopLending(userToStopLending):
#     try:
#         if session["perms"] >= 2:
#             data = db.users.find_one({"username": userToStopLending})
#             if data.items():
#                 for k, v in data.items():
#                     if k == "folderBorrowing":
#                         j = len(v)
#                         while j > 0:
#                             if (v[j-1]) == userToStopLending:
#                                 db.users.update_one({"username": userToStopLending}, {"$push": {"folderBorrowing":{v[j-1]: v[j-1]}}})
#                                 db.users.update_one({"username": userToStopLending}, {"$pull": {"folderBorrowing":{v[j-1]: v[j-1]}}})
#                                 j-=1
#                             else:
#                                 j-=1
#                     else:
#                         pass
#                 return render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], folderLended=session["folderLended"])
#             else:
#                 flash("YOU WHAT MATE")
#                 render_template("checkLending.html", folderBorrowing=session["folderBorrowing"], folderLended=session["folderLended"])
#     except:
#         return render_template("denied.html")

# Admin page redirect
@app.route("/adminChange", methods=["GET", "POST"])
def adminChange():
    try:
        if session["perms"] == 3:
            data = db.users.find({"perms" : {"$gte":0,"$lte":2}})
            return render_template("/adminEdit.html", data=data)
        if session["perms"] == 4:
            data = db.users.find({"perms" : {"$gte":0,"$lte":3}})
            return render_template("/adminEdit.html", data=data)
    except:
        return render_template("/adminEdit.html", data=data)

# Admin delete user:
@app.route("/adminDelete/<user>", methods=["GET", "POST"])
def adminDelete(user):
    data = db.users.find({"perms" : {"$gte":0,"$lte":3}})
    # Convert _id str to ObjectId
    oid = ObjectId(user)
    # Apply changes
    db.users.delete_one({"_id":oid})
    return render_template("/adminEdit.html", data=data)

# Admin set perms:
def setPerms(user, futurePerms):
    data = db.users.find({"perms" : {"$gte":0,"$lte":3}})
    # Convert _id str to ObjectId
    oid_str = user
    oid = ObjectId(oid_str)
    # Apply changes
    userToUpdate = {"_id":oid}
    updateTo = {"$set":{"perms":futurePerms}}
    db.users.update_one(userToUpdate, updateTo)
    return render_template("/adminEdit.html", data=data)

# Admin set perms 0
@app.route("/adminUpdate/0/<user>", methods=["GET", "POST"])
def adminUpdate0(user):
    if session["perms"] >= 3:
        return setPerms(user, 0)
    else:
        return render_template("denied.html")

# Admin set perms 1
@app.route("/adminUpdate/1/<user>", methods=["GET", "POST"])
def adminUpdate1(user):
    if session["perms"] >= 3:
        return setPerms(user, 1)
    else:
        return render_template("denied.html")

# Admin set perms 2
@app.route("/adminUpdate/2/<user>", methods=["GET", "POST"])
def adminUpdate2(user):
    if session["perms"] >= 3:
        return setPerms(user, 2)
    else:
        return render_template("denied.html")

# Admin set perms 3
@app.route("/adminUpdate/3/<user>", methods=["GET", "POST"])
def adminUpdate3(user):
    if session["perms"] == 4:
        return setPerms(user, 3)
    else:
        return render_template("denied.html")

# Ngrok setup
@app.route("/ngrokOn", methods=["GET", "POST"])
def ngrokOn():
        if session["perms"] >= 3:
            ngrok.connect(5000)
            tunnels = ngrok.get_tunnels()
            safeTunnel = tunnels[0].public_url
            print("Ngrok connected at URL", safeTunnel)
            ngrokStat = 1
            flash(Markup(f"Tunnel URL:<br><a href={safeTunnel}>{safeTunnel}</a>"))
            return render_template("/userarea.html", ngrokStat=ngrokStat)

@app.route("/ngrokOff", methods=["GET", "POST"])
def ngrokOff():
    try:
        if session["perms"] >= 3:
            ngrok.kill()
            print("Ngrok disconnected ")
            ngrokStat = 0
            flash("Ngrok tunnels disabled.")
            return render_template("/userarea.html", ngrokStat=ngrokStat)
    except:
        return render_template("denied.html")

# Run app
if __name__ == "__main__":
    app.run()