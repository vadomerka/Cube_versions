from requests import get, post, delete, put

#
# print(get('http://localhost:5000/api/v2/news').json())
# print(get('http://localhost:5000/api/v2/news/2').json())
# response = get('http://localhost:5000/api/v2/news/1000')
# print(response.status_code, response.json())
# print(get('http://localhost:5000/api/v2/news/qqq').json())
#
# print(post('http://localhost:5000/api/v2/news').json())
# #
# print(post('http://localhost:5000/api/v2/news',
#            json={'title': 'Заголовок'}).json())
# #
# print(post('http://localhost:5000/api/v2/news',
#            json={'title': 'Заголовок новой апишки',
#                  'content': 'Новая апишка',
#                  'user_id': 1,
#                  'is_private': False}).json())
# #
# print(post('http://localhost:5000/api/v2/news',
#            json={'title': 'Заголовок новой апишки 2',
#                  'content': 'Текст новости новая апишка',
#                  'user_id': 100,
#                  'is_private': False}).json())
#
# print(delete('http://localhost:5000/api/v2/news/999').json())
# # новости с id = 999 нет в базе
#
# print(delete('http://localhost:5000/api/v2/news/2').json())

print(put('http://localhost:5000/api/v2/news/4',
          json={'is_private': ""}).json())
