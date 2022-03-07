from requests import get, post, delete, put

# print(get('http://localhost:5000/courses').json())
print(get('http://localhost:5000/courses/1').json())
