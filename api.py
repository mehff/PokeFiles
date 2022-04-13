from hashlib import sha256
from flask import Flask, Response, request, render_template, flash
from wtforms import Form, StringField, TextAreaField, validators, StringField, SubmitField
import pymongo
import json

# App config
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

# Connection with local mongodb
try:
    # Mongo connection params
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS = 1000
    )
    db = mongo.GlobalStorageDB
    mongo.server_info()
# Raise exception if cannot connect
except:
    print("ERROR - Cannot connect to db")

# Routes
@app.route("/users", methods=["POST"])
@app.route("/", methods=['GET', 'POST'])
@app.route("/about")

def index():
    return render_template("/public/index.html")

# Render about
def about():
    return """
    <h1 style='color: red;'>I'm a red H1 heading!</h1>
    <p>This is a lovely little paragraph</p>
    <code>Flask is <em>awesome</em></code>
    """
# Create a user on DB
def create_user():
    try:
        encInfo = [request.form["userName"], request.form["userPw"], request.form["userPerms"]]
        print(encInfo)
        encryptedInfo = []
        for i in encInfo:
            print("BARIBERS",type(sha256(str(i).encode('utf8'))))
            print(encryptedInfo.append(sha256(str(i).encode('utf-8')).hexdigest()))
        encryptedInfo.append(request.form["userMail"])
        print("BLABERS",encryptedInfo)
        # Set user info
        user = {
            "userName":encryptedInfo[0],
            "userPw":encryptedInfo[1],
            "userPerms":encryptedInfo[2],
            "userMail":encryptedInfo[3]
        }
        # Send to DB
        dbResponse = db.users.insert_one(user)
        print(dbResponse.inserted_id)
        # # Print attrs
        # for attr in dir(dbResponse):
        #     print(attr)
        return Response(
            response=json.dumps(
                {"message":"user created",
                "id":f"{dbResponse.inserted_id}"
                }),
            status=200,
            mimetype="application/json"
        )
    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    app.run(debug=True)
