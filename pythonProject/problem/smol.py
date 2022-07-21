# res = 2 * (216**6) + 3*(36**9) - 432
# print(int(res, 5))


def converter(number, base):
    # split number in figures
    figures = [int(i, base) for i in str(number)]
    # invert oder of figures (lowest count first)
    figures = figures[::-1]
    result = 0
    # loop over all figures
    for i in range(len(figures)):
        # add the contirbution of the i-th figure
        result += figures[i] * base ** i
    return result


print(converter(36, 6))
