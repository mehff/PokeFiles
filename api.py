from hashlib import sha256
from flask import Flask, Response, request
# from flask_restful import Api, Resource
import pymongo
import json
app = Flask(__name__)

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

# Route setup
@app.route("/users", methods=["POST"])

# Create a user on DB
def create_user():
    try:
        # Set user info
        user = {
            "userName":str(request.form["userName"]),
            "userPw":str(request.form["userPw"]),
            "userPerms":str(request.form["userPerms"]),
            "userMail":request.form["userMail"]
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