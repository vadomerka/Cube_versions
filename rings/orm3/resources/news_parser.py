from flask_restful import reqparse

parserAddNews = reqparse.RequestParser()
parserAddNews.add_argument('title', required=True)
parserAddNews.add_argument('content', required=True)
parserAddNews.add_argument('is_private', required=True, type=bool)
# parserAddNews.add_argument('is_published', required=True, type=bool)
parserAddNews.add_argument('user_id', required=True, type=int)

parserEditNews = reqparse.RequestParser()
parserEditNews.add_argument('title')
parserEditNews.add_argument('content')
parserEditNews.add_argument('is_private', type=bool)
# parserEditNews.add_argument('is_published', required=True, type=bool)
