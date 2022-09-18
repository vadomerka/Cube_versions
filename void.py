def foo(n):
    s = bin(n)[2:]
    if s.count("1") % 2 == 0:
        s += "0"
        s = "10" + s[2:]
    else:
        s += "1"
        s = "11" + s[2:]
    return int(s, 2)


print(foo(6))
for i in range(10, 10000):
    if foo(i) > 40:
        print(i)
        break
