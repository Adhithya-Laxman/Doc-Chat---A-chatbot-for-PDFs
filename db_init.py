import sqlite3

# Connect to SQLite database (creates a new DB if it doesn't exist)
db_path = os.path.join(base_dir, 'db', 'chatdb2.db')
    conn = sqlite3.connect(db_path)
# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create User table with auto-increment for userid
cursor.execute('''
    CREATE TABLE User (
        userid INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(25),
        password VARCHAR(50),
        email VARCHAR(50)
    )
''')


# Create Chat table with auto-increment for chatid
cursor.execute('''
    CREATE TABLE Chat (
        userid INTEGER REFERENCES User(userid),
        chatid INTEGER REFERENCES CONNECTOR(chatid),
        query VARCHAR(5000),
        response VARCHAR(10000),
        citation VARCHAR(50),
        optionNum INTEGER CHECK (optionNum BETWEEN 1 AND 5)
    )
''')

# Create Connector table

cursor.execute('''
    CREATE TABLE Connector (
        chatid INTEGER  PRIMARY KEY AUTOINCREMENT,
        userid INTEGER REFERENCES User(userid),
        pdfpath VARCHAR(150)
    )
''')

# Commit changes and close the connection

conn.commit()
conn.close()
