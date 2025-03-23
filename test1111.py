# ЕГЭ
for i in range(26):
    print(chr(ord("A") + i), ord("A") + i - 55)


def to_number(number: list[int]):
    output = 0
    for i in number:
        output = output * 190 + i
    return output


a = []
for x in range(190):
    for y in range(190):
        number_1 = to_number([23, x, 32])
        number_2 = to_number([34, y, 10, 27])
        if (number_1 + number_2) % 189 == 0:
            a.append((x * y, (number_1 + number_2) / 189))
print(max(a)[1])
