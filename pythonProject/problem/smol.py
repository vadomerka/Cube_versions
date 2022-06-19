from requests import get, post, delete, put
print(get("http://localhost:5000/rest_users").json())
