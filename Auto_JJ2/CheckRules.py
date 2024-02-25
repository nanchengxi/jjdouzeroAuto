from collections import Counter


def is_sequence_string(cards):
    # 判断字符串是否连续
    card_values = {"3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14,
                   "2": 15, "X": 16, "D": 17}
    cards_list = list(cards)
    cards_list.sort(key=lambda x: card_values[x])
    for i in range(1, len(cards_list)):
        if card_values[cards_list[i]] - card_values[cards_list[i - 1]] != 1:
            return False
    return True


def is_feiji_string(string):
    # 判断3连
    result = []
    for char in string:
        if string.count(char) == 3 and char not in result:
            result.append(char)
    if result:
        return is_sequence_string(result)
    else:
        return False


def max_char_count(string):
    # 判断字符串出现的次数
    char_count = Counter(string)
    most_common = char_count.most_common(1)
    max_char = most_common[0][0]
    max_count = most_common[0][1]
    return max_count


def check_cards(cards):
    # 将牌按照点数从小到大排序
    cards = cards.replace(" ", '')
    cards = cards.replace("-", '')
    cards = cards.replace("wait", '')
    cards = cards.replace("pass", '')
    cards = cards.replace("landlord", '')
    cards = cards.replace("farmer", '')
    try:
        cards = sorted(cards, key=lambda x: '3456789TJQKA2XD'.index(x))
    except:
        print('识别出牌错误:{}'.format(cards))
        return ""

    if len(cards) == 2 and 'X' in cards and 'D' in cards:
        return '火箭'

    if len(cards) == 1:
        return '单牌'

    if len(cards) == 2 and len(set(cards)) == 1:
        return '对牌'

    if len(cards) == 3 and len(set(cards)) == 1:
        return '三张'

    if len(cards) == 4 and len(set(cards)) == 1:
        return '炸弹'

    if len(cards) == 4 and len(set(cards)) == 2:
        return '三带一'

    if len(cards) == 5 and len(set(cards)) == 2:
        return '三带二'

    if len(cards) == 6 and max_char_count(cards) == 4 and (len(set(cards)) == 2 or len(set(cards)) == 3):
        return '四带二'

    if len(cards) == 8 and max_char_count(cards) == 4 and len(set(cards)) == 3:
        return '四带四'

    if 5 <= len(cards) == len(set(cards)) and is_sequence_string(cards):
        return '单顺'

    if len(cards) >= 6 and len(set(cards)) == len(cards) / 2 and is_sequence_string(set(cards)) and max_char_count(
            cards) == 2:
        return '双顺'

    if len(cards) >= 6 and max_char_count(cards) >= 3:
        return '三顺'

    if len(cards) >= 6 and len(cards) / len(set(cards)) == 3 and is_sequence_string(set(cards)):
        return '飞机'

    if len(cards) >= 8 and is_feiji_string(cards) and len(cards) % 3 == 0:
        return '飞机带翅膀'

    else:
        return None


if __name__ == '__main__':
    cards = "33322"
    result = check_cards(cards)
    print(result)
