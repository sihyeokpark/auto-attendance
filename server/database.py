import sqlite3

import os

file_name = 'schedule1.db'

fileFlag = False
if os.path.isfile(file_name) :
    fileFlag = True


## DB open
con = sqlite3.connect('schedule1.db')
cursor = con.cursor()
## DB Create
if not fileFlag :
    cursor.execute("CREATE TABLE schedule(Id int, Date text, Time text, Who text, Notice text)")

# schedule db에서 data를 불러온다..
cursor.execute("INSERT INTO schedule VALUES (1, '월요일', '12:00', '1', '아아')")
cursor.execute("SELECT * FROM schedule")
rows = cursor.fetchall()
print(rows)
cursor.execute(f"DELETE FROM schedule WHERE id=1;")
con.commit()
cursor.execute("SELECT * FROM schedule")
rows = cursor.fetchall()
print(rows)

con.commit()
con.close()
