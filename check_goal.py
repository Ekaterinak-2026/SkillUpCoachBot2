import sqlite3
db = sqlite3.connect('skillup.db')
cols = [r[1] for r in db.execute("PRAGMA table_info(users)")]
print("goal есть:", "goal" in cols)