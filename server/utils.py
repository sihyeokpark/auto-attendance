# 깨지는 글자
def removeBreakText(data):
    msg = data.decode("utf-8")
    if msg == '':
        return ''
    i = 0
    while not 'a' <= msg[i] <= "z" or 'A' <= msg[i] <= 'Z':
        i += 1
    if i == 0:
        msg = msg
    else:
        msg = msg[(i-1):]
    return msg