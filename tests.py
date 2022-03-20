import random

n = 10
summa = 0
print(n)
for i in range(n):
    num = random.randint(-100000, 100000)
    print(num)
    summa += num * (-1)**i
print(summa)
# 160558
