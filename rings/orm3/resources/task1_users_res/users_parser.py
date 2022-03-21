from flask_restful import reqparse

parserAddUser = reqparse.RequestParser()
parserAddUser.add_argument('surname', required=True)
parserAddUser.add_argument('name', required=True)
parserAddUser.add_argument('age', required=True)
parserAddUser.add_argument('position', required=True)
parserAddUser.add_argument('speciality', required=True)
parserAddUser.add_argument('address', required=True)
parserAddUser.add_argument('email', required=True)
parserAddUser.add_argument('password', required=True)
parserAddUser.add_argument('password_again', required=True)
