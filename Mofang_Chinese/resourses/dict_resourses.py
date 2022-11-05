from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.words import Words, WordsToUsers
from resourses.parser import parserAddWord
from data.courses import Courses, users_to_course
from data.users import User
from flask import request
import os


def abort_if_not_found(id):
    session = db_session.create_session()
    word = session.query(Words).get(id)
    if not word:
        abort(404, message="Object not found", id=id)


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
        path = "static/words_data/"
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
                pass
                # print(f"The file {filename} does not exist")
        session.delete(word)
        session.commit()
        return jsonify({'success': 'OK'})


class WordViewRecordingResource(Resource):
    def post(self, user_id, word_id):
        session = db_session.create_session()
        word_to_user = session.query(WordsToUsers).filter(WordsToUsers.users == user_id,
                                                          WordsToUsers.words == word_id).first()
        if not word_to_user:
            abort(404, message=f"User {user_id} or word {word_id} not found")
        if word_to_user.learn_state == 0:
            word_to_user.learn_state = 1
        session.merge(word_to_user)
        session.commit()
        session.close()
        return jsonify({'success': 'OK'})
