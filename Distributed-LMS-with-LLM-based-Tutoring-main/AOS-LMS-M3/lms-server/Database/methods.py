import json
import sqlite3
import uuid

def get_dict_factory():
    return lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])

def gen_uuid():
    return str(uuid.uuid4())
# def validate_user(email,password,role):
#     pass
    # with open("lms_db.json", "r") as f:
    #     data = json.load(f)
    #     user = data.get(role)
    #     _index = user["_index"].get(f"{email}")
    #     try:
    #         if user["_data"][_index].get("password") == password:
    #             return True,user["_data"][_index].get("courses",[]),user["_data"][_index].get("id")
    #         else:
    #             return False,None,None
    #     except Exception as e:
    #         return False,None,None

def validate_user(conn,user,password,role):
    query = """SELECT u.id FROM 
                    users u  LEFT JOIN roles r
                        ON
                        u.role_id = r.id  
                            WHERE 
                            (email = ? OR username = ?)AND password = ? AND r.name = ?
                    LIMIT 1"""

    cursor = conn.cursor()
    cursor.execute(query,(user,user,password,role,))
    id = cursor.fetchone()
    if id is None:
        return False,None,None
    else:
        return True,"AOS",id[0]

def add_material(conn,course_id,name,filename):
    try:
        query = """INSERT INTO materials(id,name,course_id,file_name,created_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)"""
        cursor = conn.cursor()
        cursor.execute(query,(gen_uuid(),name,course_id,filename,))

    except Exception as e:
        print(e)
        conn.rollback()
        return e

def get_course_materials(conn,course_id):
    try:
        query = """SELECT m.id as material_id,m.name as material_name,m.file_name as filename
                    FROM materials m
                    WHERE m.course_id = ?"""
        cursor = conn.cursor()
        cursor.execute(query,(course_id,))
        return cursor.fetchall(),None
    except Exception as error:
        print(error)
        return None,error



def get_material(conn,material_id):
    try:
        query = """SELECT m.name,m.file_name,m.course_id FROM materials m WHERE m.id = ?"""
        cursor = conn.cursor()
        cursor.execute(query,(material_id,))
        return cursor.fetchone(),None
    except Exception as error:
        return None,error


def insert_assignment(conn,name,due_date,description,course_id):
    try:
        query = """INSERT  INTO assignments(id, name, due_date, description, course_id, created_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)"""
        cursor = conn.cursor()
        cursor.execute(query,(gen_uuid(),name,due_date,description,course_id,))
        conn.commit()
        return None

    except Exception as error:
        conn.rollback()
        return error

def insert_assignment_submission(conn,assignment_id,student_id,filename):
    try:
        query = """INSERT OR REPLACE INTO assignment_submissions(assignment_id, user_id,filename,created_at) VALUES (?,?,?,CURRENT_TIMESTAMP)"""
        cursor = conn.cursor()
        cursor.execute(query,(assignment_id,student_id,filename,))

    except Exception as error:
        conn.rollback()
        return error

def select_assignments(conn,course_id):
    try:
        columns = ("id","name","due_date","description")
        query = """SELECT id,name,due_date,description FROM assignments WHERE course_id = ?"""
        cursor = conn.cursor()
        cursor.execute(query,(course_id,))
        data = cursor.fetchall()
        assignments = [{columns[i]:record[i] for i in range(len(record))} for record in data]
        return assignments,None
    except Exception as error:
        return None , error

def insert_query(conn,query_text,posted_by,course_id):
    try:
        id = gen_uuid()

        query = """INSERT INTO queries(id, query_text, posted_by,course_id, created_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)"""
        cursor = conn.cursor()
        cursor.execute(query,(id,query_text,posted_by,course_id,))
        conn.commit()
    except Exception as error:
        print(error)
        return error





def select_queries(conn,course_id):
    try:
        conn.row_factory = get_dict_factory()
        query = """SELECT ques.id,ques.query_text,ques.posted_by,ques.reply,u2.username as replied_by
        FROM  (SELECT queries.id, query_text, users.username as posted_by,reply,reply_by,course_id
              FROM queries LEFT JOIN users ON posted_by = users.id
              WHERE course_id = ?) as ques
        LEFT JOIN users u2 ON u2.id = ques.reply_by
         """
        cursor = conn.cursor()
        cursor.execute(query,(course_id,))
        conn.commit()
        return cursor.fetchall(),None
    except Exception as error:
        return None , error

def update_answer_to_query(conn,query_id,answer,userid):
    try:
        query = "UPDATE queries SET reply=? , reply_by = ? WHERE id = ? "
        cursor = conn.cursor()
        cursor.execute(query, (answer, userid, query_id))
        conn.commit()
        return None
    except Exception as error:
        print(error)
        return error