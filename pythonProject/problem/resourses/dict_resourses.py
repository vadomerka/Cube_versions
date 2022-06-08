from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.words import Words
from resourses.parser import parserAddWord
from data.courses import Courses, users_to_course
from data.users import User
from flask import request
import os


def abort_if_not_found(word_id):
    session = db_session.create_session()
    word = session.query(Words).get(word_id)
    if not word:
        abort(404, message=f"Word {word_id} not found")


class DictResourse(Resource):
    def get(self):
        session = db_session.create_session()
        dictionary = session.query(Words).all()
        # print(dictionary[0]["author"])
        ret = {'words': [item.to_dict(
            only=("id",
                  "author",
                  "hieroglyph",
                  "translation",
                  "front_side",
                  "left_side",
                  "right_side",
                  "up_side",
                  "down_side",
                  "front_side_audio",
                  "right_side_audio",
                  "up_side_audio")) for item in dictionary]}
        return jsonify(ret)

    def post(self):
        if not request.json:
            return jsonify({'error': 'Empty request'})
        elif not all(key in request.json for key in
                     ["id",
                      "hieroglyph",
                      "tranlation",
                      "front_side",
                      "left_side",
                      "right_side",
                      "up_side",
                      "down_side",
                      "front_side_audio",
                      "right_side_audio",
                      "up_side_audio"
                      ]):
            return jsonify({'error': 'Bad request'})
        args = parserAddWord.parse_args()
        session = db_session.create_session()

        word = Words(id=args["id"],
                     hieroglyph=args["hieroglyph"],
                     tranlation=args["tranlation"],
                     front_side=args["front_side"],
                     left_side=args["left_side"],
                     right_side=args["right_side"],
                     up_side=args["up_side"],
                     down_side=args["down_side"],
                     front_side_audio=args["front_side_audio"],
                     right_side_audio=args["right_side_audio"],
                     up_side_audio=args["up_side_audio"]
                     )
        session.add(word)
        session.commit()
        return jsonify({'success': 'OK'})


class WordResourse(Resource):
    def get(self, word_id):
        abort_if_not_found(word_id)
        session = db_session.create_session()
        word = session.query(Words).get(word_id)

        ret = {'word': word.to_dict(
            only=("id",
                  "author",
                  "hieroglyph",
                  "translation",
                  "front_side",
                  "left_side",
                  "right_side",
                  "up_side",
                  "down_side",
                  "front_side_audio",
                  "right_side_audio",
                  "up_side_audio"))}
        return jsonify(ret)

    def delete(self, word_id):
        abort_if_not_found(word_id)
        session = db_session.create_session()
        word = session.query(Words).get(word_id)
        path = "static/"
        for name in (word.front_side,
                     word.left_side,
                     word.right_side,
                     word.front_side_audio,
                     word.right_side_audio,
                     word.up_side_audio):
            filename = path + str(name)
            print(filename)
            if os.path.exists(filename):
                os.remove(filename)
            else:
                print(f"The file {filename} does not exist")
        for name in (word.up_side, word.down_side):
            name = name.split(".")
            name_0 = ".".join([name[0] + "_0", name[1]])
            name_90 = ".".join([name[0] + "_90", name[1]])
            name_180 = ".".join([name[0] + "_180", name[1]])
            name_270 = ".".join([name[0] + "_270", name[1]])
            for name_ in (name_0, name_90, name_180, name_270):
                filename = path + name_
                print(filename)
                if os.path.exists(filename):
                    os.remove(filename)
                else:
                    print(f"The file {filename} does not exist")
        session.delete(word)
        session.commit()
        return jsonify({'success': 'OK'})
