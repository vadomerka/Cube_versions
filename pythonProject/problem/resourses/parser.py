from flask_restful import reqparse

parserAdd = reqparse.RequestParser()
parserAdd.add_argument('name', required=True)
parserAdd.add_argument('about', required=True)
