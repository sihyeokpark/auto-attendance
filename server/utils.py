# 깨지는 글자
def removeBreakText(data):
    msg = data.decode("utf-8")
    i = 0
    while not 'a' <= msg[i] <= "z" or 'A' <= msg[i] <= 'Z':
        i += 1
    msg = msg[i:]
    return msg