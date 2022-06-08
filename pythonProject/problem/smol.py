import os
name = "static/1delete_me.txt"
if os.path.exists(name):
    os.remove(name)
else:
    print("The file does not exist")
