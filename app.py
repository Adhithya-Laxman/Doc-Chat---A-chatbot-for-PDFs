from flask import Flask, request, jsonify, render_template
from model import PDFChat_RAG
import os
import sqlite3
import markdown
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
model = PDFChat_RAG()
# db.create_all()
pdf_path = None
# app.app_context().push()
# Home page endpoint
def get_db_connection():
    conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        # Query to fetch user with provided username and password
        cursor.execute('SELECT * FROM User WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            # Redirect to some authenticated page
            # Accessing the userid using dictionary key
            return redirect(url_for('authenticated', userid=user['userid']))
        else:
            # If user does not exist or password is incorrect, show error message
            error = 'Invalid username or password. Please try again.'
            return render_template('login.html', error=error)
    # If GET request, render the login form
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert new user into User table
        cursor.execute('INSERT INTO User (username, password, email) VALUES (?, ?, ?)', (username, password, email))
        conn.commit()
        conn.close()
        # Redirect to login page after successful signup
        return redirect(url_for('login'))
    # If GET request, render the signup form
    return render_template('signup.html')

@app.route('/<userid>', methods=['GET', 'POST'])
def authenticated(userid):
    # Cast userid to integer
    
    if userid == 'favicon.ico':
        return ""
    userid = int(userid)
    # Fetch username from the database using userid
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM User WHERE userid = ?', (userid,))
    user = cursor.fetchone()
    username = user['username'] if user else None
    
    # Fetch all records corresponding to the user from the Connector table
    cursor.execute('SELECT chatid, pdfpath FROM Connector WHERE userid = ?', (userid,))
    connector_records = cursor.fetchall()
    print(connector_records, userid)

    pdf_path = []
    for val in connector_records:
        pdf_path.append(val['pdfpath'])

    if request.method == 'POST':
        cursor.execute('select count(*) from connector')
        chatid = cursor.fetchone()[0]
        cursor.execute('INSERT INTO Connector (userid,pdfpath) VALUES ( ?, ?)', (userid, None))
        conn.commit()
        cursor.execute('select count(*) from connector')
        chatid = cursor.fetchone()[0]
        print(chatid)

        conn.close()
        
        return redirect(url_for('user_chats', userid= userid, chatid=chatid ))
    
        # return render_template('chatpage.html', userid= userid, chatid=records[0] )
    # Close the database connection

    print('UID',userid)
    conn.close()
    pdf_name = []
    for val in pdf_path:

        if val is not None:
            pdf_name.append(val.split('/')[-1])
    res = []
    for val in connector_records:
        if val['pdfpath'] is not None:
            res.append(val)
    

    return render_template('dashboard.html', userid=userid, username=username, chat_record=res, pdf_name = pdf_name)



@app.route('/chat/<userid>/<chatid>', methods=['GET', 'POST'])
def user_chats(userid, chatid):
    name = 'temporary'

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                name = file.filename.split(' ')
                name = '_'.join(name)
                base_dir = os.getcwd()
                pdf_path = f'{base_dir}/PDFChat/static/{file.filename}'
                file.save(pdf_path)
                
                conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')

                cursor = conn.cursor()
                cursor.execute('Update Connector set pdfpath = ? where userid=? and chatid = ?', (pdf_path, userid,chatid))
                conn.commit()
                cursor.execute("SELECT * FROM chat")

                chats = cursor.fetchall()

                chat_data = []
                for chat in chats:
                    if "|---|---|" in chat[3]:
                        chat_data.append({
                            'chat_id': chat[0],  
                            'userid': chat[1], 
                            'query': markdown.markdown(chat[2]), 
                            'response': markdown.markdown(chat[3], extensions=['markdown.extensions.tables']),
                            'citation': chat[4]
                            
                        })
                    else:
                        chat_data.append({
                        'chat_id': chat[0],  
                        'userid': chat[1], 
                        'query': markdown.markdown(chat[2]), 
                        'response': markdown.markdown(chat[3]),
                        'citation': chat[4]
                        
                        })
                cursor.execute('SELECT * from Connector where userid= ? and chatid= ?',(userid,chatid))
                pdf_file = cursor.fetchone()
                print(pdf_file)
                pdf_path_present = False
                if pdf_file[2] is not None:
                    pdf_path_present = True
                print(pdf_path_present)
                cursor.close()
                conn.close()
                model.initialize_model(pdf_path, name)
                val = None
                if pdf_path_present:
                    val  =pdf_file[2].split('/')[-1]

                return render_template('chatpage.html',chats=chat_data, pdf_path=val, userid=userid, chatid = chatid, pdf_path_present = pdf_path_present)

        else:
            data = request.form
            # print(data)
            option = int(data.get('option'))
            print("OPTTTTTTTTTTT",option)
            query = data.get('query', '')

            conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')
                #print("HEYYYYYYYYYYYYY", pdf_path)

            cursor = conn.cursor()
            cursor.execute('SELECT pdfpath FROM Connector WHERE userid = ? AND chatid = ?',(userid, chatid))
            pdf_path = cursor.fetchone()[0]
            #pdf_path = "/home/adminroot/Desktop/2105001/hackathon/PDFChat/static/Linux Pocket Guide.pdf"
            # print

            if not option or not query:
                return jsonify({'error': 'Missing option or query'})
            # print(query,option)

            # print(pdf_path.split('/')[-1])
            result_pages, response = model.run(option, query, pdf_path, 'temporary')
            
            conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')
            cursor = conn.cursor()

            sql_insert = """
                INSERT INTO Chat (userid, chatid, query, response, citation, optionNum)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            # print(name)
            
            values = (userid, chatid, query, response, str(result_pages), option)  
            cursor.execute(sql_insert, values)

            
            conn.commit()
            conn.close()
            conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')

            cursor = conn.cursor()

            cursor.execute("SELECT * FROM chat")

            chats = cursor.fetchall()
            # print(chat)

            chat_data = []
            for chat in chats:
                if "|---|---|" in chat[3]:
                    chat_data.append({
                        'chat_id': chat[0],  
                        'userid': chat[1], 
                        'query': markdown.markdown(chat[2]), 
                        'response': markdown.markdown(chat[3], extensions=['markdown.extensions.tables']),
                        'citation': chat[4]
                        
                    })
                else:
                    chat_data.append({
                    'chat_id': chat[0],  
                    'userid': chat[1], 
                    'query': markdown.markdown(chat[2]), 
                    'response': markdown.markdown(chat[3]),
                    'citation': chat[4]
                    
                    })
            cursor.execute('SELECT * from Connector where userid= ? and chatid= ?',(userid,chatid))
            pdf_file = cursor.fetchone()
            print(pdf_file)
            pdf_path_present = False
            if pdf_file[2] is not None:
                pdf_path_present = True
            print(pdf_path_present)
            cursor.close()
            conn.close()
            print("PATHHHHHHHHHHHHHHHHH",pdf_path)
            val = None
            if pdf_path_present:
                val  =pdf_file[2].split('/')[-1]

            return render_template('chatpage.html',chats=chat_data, pdf_path=val, userid = userid, chatid = chatid, pdf_path_present = pdf_path_present)
        #return render_template('chatpage.html',chats=chat_data, pdf_path=pdf_path)


    # Fetch username from the database using userid
    conn = sqlite3.connect('/home/adminroot/Desktop/2105001/hackathon/PDFChat/db/chatdb2.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM chat where chatid = (?)", (chatid,))
    chats = cursor.fetchall()

    # chat_data = []
    # # print("CHATS",chats)
    # for chat in chats:
    #     chat_data.append({
    #         'chat_id': chat[0],  
    #         'userid': chat[1], 
    #         'query': markdown.markdown(chat[2]), 
    #         'response': markdown.markdown(chat[3]),
    #         'citation': chat[4]
    #     })

    chat_data = []
    for chat in chats:
        if "|---|---|" in chat[3]:
            chat_data.append({
                'chat_id': chat[0],  
                'userid': chat[1], 
                'query': markdown.markdown(chat[2]), 
                'response': markdown.markdown(chat[3], extensions=['markdown.extensions.tables']),
                'citation': chat[4]
                
            })

        else:
            chat_data.append({
            'chat_id': chat[0],  
            'userid': chat[1], 
            'query': markdown.markdown(chat[2]), 
            'response': markdown.markdown(chat[3]),
            'citation': chat[4]
            
            })
    
    cursor.execute('SELECT * from Connector where userid= ? and chatid= ?',(userid,chatid))
    pdf_file = cursor.fetchone()
    print(pdf_file)
    pdf_path_present = False
    if pdf_file[2] is not None:
        pdf_path_present = True
    print(pdf_path_present)
    cursor.close()
    conn.close()
    # print("CHATDATA",chat_data)
    val = None
    if pdf_path_present:
         val  =pdf_file[2].split('/')[-1]
    return render_template('chatpage.html',chats = chat_data, pdf_path_present=pdf_path_present, userid = userid, chatid = chatid, pdf_path =val)




if __name__ == '__main__':
    app.run(debug=True)




