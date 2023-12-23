import random



def test(pains):
    ok = True
    used_keys = []
    used_values = []
    for item in pains:
        if item[0] == item[1]:
            print("DUPLICATED")
            ok = False
        if item[0] in used_keys:
            print("DUPLICATED KEY")
        if item[1] in used_values:
            print("DUPLICATED VALUE")
        used_keys.append(item[0])
        used_values.append(item[1])
    if len(used_keys) != 5:
        print("INVALID LENGTH", len(used_keys))
    if not ok:
        print(pains)
    print("OK:", ok)
    return ok


if __name__ == '__main__':
    numbers = [1, 2, 3, 4, 5]
    ok = True
    while ok:
        ok = test(get_random_pairs(numbers))
