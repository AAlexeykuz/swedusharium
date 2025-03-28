a = {
    "3": [
        {"time": 2, "pon": 3},
        {"time": 3, "pon": 0},
    ],
    "1": [
        {"time": 1, "pon": 1},
    ],
    "2": [
        {"time": 2, "pon": 0},
        {"time": 6, "pon": 2},
        {"time": 2, "pon": 0},
    ],
}


a = {
    k: sorted(v, key=lambda x: x["time"], reverse=True)
    for k, v in sorted(a.items(), reverse=True)
}


print(a)
