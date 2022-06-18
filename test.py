def removeBreakText(data):
    msg = data
    i = 0
    while not 'a' <= msg[i] <= "z" or 'A' <= msg[i] <= 'Z':
        i += 1
    msg = msg[i:]
    return msg
print(removeBreakText('�d�/dd'))