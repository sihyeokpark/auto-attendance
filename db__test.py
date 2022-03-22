import sqlite3

# SQLite DB 연결
with sqlite3.connect("user.db") as conn:
    conn = sqlite3.connect("user.db")

    # Connection 으로부터 Cursor 생성
    cur = conn.cursor()

    qury = "CREATE TABLE IF NOT EXISTS user \
        (id text PRIMARY KEY, pwd text)"
    cur.execute(qury)

    # 데이터 입력  INSERT

    qury = "INSERT INTO user(id, pwd) VALUES('exon','exon')"
    cur.execute(qury)

    id = 'exon'
    qury = "SELECT * FROM user WHERE id='%s'"%id
    cur.execute(qury)

    result = []
    for data in cur.fetchone():
        result.append(data)

    print("id = " + str(result[0]))
    print("pwd = " + str(result[1]))

conn.close()