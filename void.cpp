#include <iostream>
#include <vector>
using namespace std;

int main()
{
    int m = 0, n = 0, jump = 0;
    cin >> m >> n;
    vector<pair<int, int>> dp(n, {0, 0});
    vector<pair<int, int>> dp1(n, {0, 0});
    for (int i = 0; i < n; i++) {
        cin >> dp[i].first >> dp[i].second;
    }
    int min_sum = 1000000;
    int summa = 0;
    for (int i = 0; i < n; i++) {
        // cout << dp[i].first << " " << dp[i].second << "\n";
        dp1 = dp;
        summa = 0;
        for (int j = 0; j < n; j++) {
            if (i == j) continue;
            else if (i > j){
                if (dp1[j].second < dp1[j + 1].first){
                    jump = dp1[j + 1].first - dp1[j].second;
                    dp1[j].first += jump;
                    dp1[j].second += jump;
                    summa += jump;
                }
                else if (dp1[j].first > dp1[j + 1].second){
                    jump = dp1[j].first - dp1[j + 1].second;
                    dp1[j].first -= jump;
                    dp1[j].second -= jump;
                    summa += jump;
                }
            }else{
                if (dp1[j - 1].second < dp1[j].first){
                    jump = dp1[j].first - dp1[j - 1].second;
                    dp1[j].first -= jump;
                    dp1[j].second -= jump;
                    summa += jump;
                }
                else if (dp1[j - 1].first > dp1[j].second){
                    jump = dp1[j - 1].first - dp1[j].second;
                    dp1[j].first += jump;
                    dp1[j].second += jump;
                    summa += jump;
                }
            }
        }
        min_sum = min(min_sum, summa);
    }
    cout << min_sum;
    return 0;
}

