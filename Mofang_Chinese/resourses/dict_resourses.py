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
                  "transcription",
                  "phrase_ch",
                  "phrase_ru",
                  "image",
                  "front_side_audio",
                  "left_side_audio",
                  "right_side_audio",
                  "up_side_audio",
                  "down_side_audio")) for item in dictionary]}
        return jsonify(ret)

    def post(self):
        # print(request.json)
        if not request.json:
            return jsonify({'error': 'Empty request'})
        elif not all(key in request.json for key in
                     ["author",
                      "hieroglyph",
                      "translation",
                      "transcription",
                      "phrase_ch",
                      "phrase_ru",
                      "image",
                      "front_side_audio",
                      "left_side_audio",
                      "right_side_audio",
                      "up_side_audio",
                      "down_side_audio"]):
            # print(2)
            return jsonify({'error': 'Bad request'})
        # print(3)
        args = parserAddWord.parse_args()
        session = db_session.create_session()
        # print(args)
        word = Words(author=args["author"],
                     hieroglyph=args["hieroglyph"],
                     translation=args["translation"],
                     front_side=args["transcription"],
                     left_side=args["phrase_ch"],
                     right_side=args["phrase_ru"],
                     up_side=args["image"],
                     front_side_audio=args["front_side_audio"],
                     left_side_audio=args["left_side_audio"],
                     right_side_audio=args["right_side_audio"],
                     up_side_audio=args["up_side_audio"],
                     down_side_audio=args["down_side_audio"]
                     )
        print(word)
        print(4)
        session.add(word)
        session.commit()
        print(5)
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
                  "transcription",
                  "phrase_ch",
                  "phrase_ru",
                  "image",
                  "front_side_audio",
                  "left_side_audio",
                  "right_side_audio",
                  "up_side_audio",
                  "down_side_audio",))}
        return jsonify(ret)

    def delete(self, word_id):
        abort_if_not_found(word_id)
        session = db_session.create_session()
        word = session.query(Words).get(word_id)
        path = "static/"
        side_list = []
        for x in [word.image,
                  word.front_side_audio,
                  word.left_side_audio,
                  word.right_side_audio,
                  word.down_side_audio,
                  word.up_side_audio]:
            if "undefined" not in x:
                side_list.append(x)

        for name in side_list:
            filename = path + str(name)
            # print(filename)
            if os.path.exists(filename):
                os.remove(filename)
            else:
                print(f"The file {filename} does not exist")
        session.delete(word)
        session.commit()
        return jsonify({'success': 'OK'})
