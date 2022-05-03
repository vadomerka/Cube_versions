from requests import get, post, delete, put

# print(get("http://127.0.0.1:5000/rest_user/"))
for i in range(1, 5):
    print(get('http://localhost:5000/rest_user/' + str(i)).json())
