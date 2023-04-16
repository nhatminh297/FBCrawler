import pyodbc
import logging

def create_cursor(server, database):
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';Trusted_Connection=yes;', autocommit=True)
    cursor = cnxn.cursor()
    return cursor, cnxn

def check_database(server, database):
    cursor, cnxn = create_cursor(server, database = "master")

    database_create_query = f"""
    IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = '{database}')
        CREATE DATABASE {database}
    """
    cursor.execute(database_create_query)
    cnxn.close()

def check_table(server, database, desktop_user):
    cursor, cnxn = create_cursor(server, database)
    cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON DATABASE::{database} TO [{desktop_user}]")
    posts_exists_query = "SELECT * FROM sysobjects WHERE name='posts' AND xtype='U'"
    cursor.execute(posts_exists_query)
    posts_exists = cursor.fetchone() is not None

    if not posts_exists:
        cursor.execute("""
            CREATE TABLE posts (
                post_id VARCHAR(20) PRIMARY KEY,
                page_id VARCHAR(20),
                actor_id VARCHAR(20),
                content NVARCHAR(MAX),
            )
        """)
    else:
        print("posts table checked")

    comments_exists_query = "SELECT * FROM sysobjects WHERE name='comments' AND xtype='U'"
    cursor.execute(comments_exists_query)
    comments_exists = cursor.fetchone() is not None

    if not comments_exists:
        cursor.execute("""
            CREATE TABLE comments (
                comment_id VARCHAR(20) PRIMARY KEY,
                post_id VARCHAR(20),
                author NVARCHAR(100),
                message NVARCHAR(MAX),
                FOREIGN KEY (post_id) REFERENCES posts(post_id)
            )
        """)
    else:
        print("comments table checked")
    reps_exists_query = "SELECT * FROM sysobjects WHERE name='replies' AND xtype='U'"
    cursor.execute(reps_exists_query)
    reps_exists = cursor.fetchone() is not None

    if not reps_exists:
        cursor.execute("""
            CREATE TABLE replies (
                rep_id VARCHAR(255) PRIMARY KEY,
                rep_to VARCHAR(20),
                rep_author NVARCHAR(100),
                rep_message NVARCHAR(MAX),
                FOREIGN KEY (rep_to) REFERENCES comments(comment_id)
            )
        """)
    else:
        print("reps table checked")
    cnxn.close()
    

def check(server, database, desktop_user):
    check_database(server, database)
    check_table(server, database, desktop_user)

def post_exists(cursor, post_data):
    cursor.execute("SELECT * FROM posts WHERE post_id = ?", post_data['post_id'])
    result = cursor.fetchone()
    return result is not None


def store_post(cursor, post_data):
    cursor.execute("SELECT * FROM posts WHERE post_id = ?", post_data['post_id'])
    row = cursor.fetchone()
    if row is None:
        try:
            cursor.execute("INSERT INTO posts (post_id, page_id, actor_id, content) VALUES (?, ?, ?, ?)",
                            post_data['post_id'], post_data['page_id'], post_data['actor_id'], post_data['content'])
            # print("store post success")
        except pyodbc.Error as e:
            logging.error(f"An error occurred: {e}")


def store_cmt(cursor, cmt_info):
    cursor.execute("SELECT * FROM comments WHERE comment_id = ?", cmt_info['comment_id'])
    row = cursor.fetchone()
    if row is None:
        try:
            cursor.execute("INSERT INTO comments (comment_id, post_id, author, message) VALUES (?, ?, ?, ?)",
                            cmt_info['comment_id'], cmt_info['post_id'], cmt_info['author'], cmt_info['message'])
            # print("store comment success")
        except pyodbc.Error as e:
            logging.error(f"An error occurred: {e}")


def store_rep(cursor, rep):
    cursor.execute("SELECT * FROM replies WHERE rep_id = ?", rep['rep_id'])
    row = cursor.fetchone()
    if row is None:
        try:
            cursor.execute("INSERT INTO replies(rep_id, rep_to, rep_author, rep_message) VALUES (?, ?, ?, ?)",
                            rep['rep_id'], rep['rep_to'], rep['rep_author'], rep['rep_message'])
            # print("store rep success")
        except pyodbc.Error as e:
            logging.error(f"An error occurred: {e}")