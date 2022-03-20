from requests import get, post, delete, put

# print(get('http://localhost:5000/courses').json())
# print(post('http://localhost:5000/courses',
#            json={'id': 2,
#                  'name': "Радомир",
#                  "about": "тест отдыха"
#                  }).json())
print(delete('http://localhost:5000/courses/1').json())
print(get('http://localhost:5000/courses').json())
