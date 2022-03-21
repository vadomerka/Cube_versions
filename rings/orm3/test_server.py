from requests import get, post, delete, put

# print(get('http://localhost:5000/api/news').json())
# print(get('http://localhost:5000/api/news/1').json())
# print(get('http://localhost:5000/api/news/1000').json())
# print(get('http://localhost:5000/api/news/qqq').json())
#
# print(post('http://localhost:5000/api/news').json())
#
# print(post('http://localhost:5000/api/news',
#            json={'title': 'Заголовок'}).json())
#
# # print(post('http://localhost:5000/api/news',
# #            json={'title': 'Заголовок',
# #                  'content': 'Текст новости',
# #                  'user_id': 1,
# #                  'is_private': False}).json())
#
# # print(post('http://localhost:5000/api/news',
# #            json={'title': 'Заголовок',
# #                  'content': 'Текст новости',
# #                  'user_id': 100,
# #                  'is_private': False}).json())
#
# print(delete('http://localhost:5000/api/news/999').json())
# # новости с id = 999 нет в базе
#
# print(delete('http://localhost:5000/api/news/1').json())

# print(put('http://localhost:5000/api/news/2',
#           json={'is_private': "gdfgdfg"}).json())
