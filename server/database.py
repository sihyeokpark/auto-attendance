import sqlite3

con = sqlite3.connect('schedule.db')
cursor = con.cursor()
cursor.execute("CREATE TABLE schedule(Id int, Date text, Time text, Who text, Notice text)")
con.commit()
con.close()