k = 4
for x in range(22 * k, 75 * k):
    x /= k
    B = 23 <= x <= 37
    C = 41 <= x <= 73
    A = False
    if not (((not B) <= C) <= A):
        print(x)
    else:
        print()
