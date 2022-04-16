n = int(input())
# 1 -> n
dp = [(0, 0)] * (n + 1)
dp[1] = (0, 0)  # 0 1 0 0 0 0
# Умножить число X на 2.
# Умножить число X на 3.
# Прибавить к числу X единицу.
for i in range(2, n + 1):
    dp[i] = (dp[i - 1][0], i - 1)
    if i % 2 == 0 and dp[i // 2][0] < dp[i][0]:  # (0, 5) < (10, 50)
        dp[i] = (dp[i // 2][0], i // 2)  # (min, pred)  # 0 0 1 1
    if i % 3 == 0 and dp[i // 3][0] < dp[i][0]:
        dp[i] = (dp[i // 3][0], i // 3)
    dp[i] = (dp[i][0] + 1, dp[i][1])
# print(dp)
print(dp[n][0])
ans = [n]
pred = dp[n][1]
while pred != 0:
    ans.append(pred)
    pred = dp[pred][1]
print(*ans[::-1])
