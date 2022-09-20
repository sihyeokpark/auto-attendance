# 깨지는 글자
def removeBreakText(data):
    msg = data.decode("utf-8")
    if msg == '':
        return ''
    i = 0
    while not 'a' <= msg[i] <= "z" or 'A' <= msg[i] <= 'Z':
        i += 1
    msg = msg[i:]
    if msg.split('/')[0] == 'ogin':
        msg = msg.replace('ogin', 'Login')
    return msg