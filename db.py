import sqlite3
from operator import itemgetter

DATABASE = 'todo.db'

con = sqlite3.connect(DATABASE)

with open('schema.sql') as f:
    con.executescript(f.read())

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def list_todos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM todos")
    todos = cur.fetchall()
    results = [dict(row) for row in todos]
    return results

def insert_todo(todo):
    conn = get_db_connection()
    id, title, completed, ownerID = itemgetter('ID', 'Title', 'Completed', 'OwnerID')(todo)
    conn.execute("INSERT INTO todos VALUES (?, ?, ?, ?)", (id, title, completed, ownerID))
    conn.commit()
    conn.close()

def update_todo(todo):
    conn = get_db_connection()
    id, title, completed, ownerID = itemgetter('ID', 'Title', 'Completed', 'OwnerID')(todo)
    conn.execute("UPDATE todos SET Title=?, Completed=?, OwnerID=? WHERE ID=?", (title, completed, ownerID, id))
    conn.commit()
    conn.close()

def delete_todo(todo):
    conn = get_db_connection()
    id = todo['ID']
    conn.execute("DELETE FROM todos WHERE id=?", (id,))
    conn.commit()
    conn.close()