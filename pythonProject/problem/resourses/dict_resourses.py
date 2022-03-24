from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from data import db_session
from data.words import Words
from resourses.parser import parserAdd


def abort_if_word_not_found(word_id):
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
        args = parserAdd.parse_args()
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
        abort_if_word_not_found(word_id)
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
        abort_if_word_not_found(word_id)
        session = db_session.create_session()
        word = session.query(Words).get(word_id)
        session.delete(word)
        session.commit()
        return jsonify({'success': 'OK'})
