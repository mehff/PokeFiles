from cgi import test
from flask import Flask
from flask_restful import Api, Resource, reqparse
import pandas as pd
import ast

# Flask initialization
app = Flask(__name__)
api = Api(app)

# Parser setup for multiple uses
parser = reqparse.RequestParser()

# CSV to be upgraded to MongoDB Compass!
class Users(Resource):
    # # Reads CSV and returns dict.
    # def get(self):
    #     data = pd.read_csv('./data/users.csv')
    #     data = data.to_dict()
    #     return {'data':data},200

    # Creates user
    def post(self):

        # Add arguments to parser
        parser.add_argument('userId', required=True)
        parser.add_argument('userName', required=True)
        parser.add_argument('userPw', required=True)
        parser.add_argument('userPerms', required=True)

        # Creates dataframe with args
        args = parser.parse_args()
        new_data = pd.DataFrame([{         #--
            'userId': args['userId'],      #  | THIS DOESN'T
            'userName': args['userName'],  #  | WORK WITHOUT
            'userPw': args['userPw'],      #  | LIST WRAPPING!
            'userPerms': args['userPerms'] #--
        }])

        # Reads source file, then returns source file with new data
        data = pd.read_csv('./data/users.csv')
        data = data.append(new_data, ignore_index=True)
        return{'data': data.to_dict()},200

# Add resources to api
api.add_resource(Users, '/users')

# Ready for takeoff!
# ##############################################################
# ##### Don't forget to remove debug=True post development #####
# ##############################################################
if __name__ == "__main__":
    app.run(debug=True)