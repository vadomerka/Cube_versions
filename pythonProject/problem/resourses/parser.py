from flask_restful import reqparse

parserAdd = reqparse.RequestParser()
parserAdd.add_argument('name', required=True)
parserAdd.add_argument('about', required=True)

parserAddWord = reqparse.RequestParser()
parserAddWord.add_argument("id", required=True)
parserAddWord.add_argument("author", required=True)
parserAddWord.add_argument("hieroglyph", required=True)
parserAddWord.add_argument("translation", required=True)
parserAddWord.add_argument("front_side", required=True)
parserAddWord.add_argument("left_side", required=True)
parserAddWord.add_argument("right_side", required=True)
parserAddWord.add_argument("up_side", required=True)
parserAddWord.add_argument("down_side", required=True)
parserAddWord.add_argument("front_side_audio", required=True)
parserAddWord.add_argument("right_side_audio", required=True)
parserAddWord.add_argument("up_side_audio", required=True)
