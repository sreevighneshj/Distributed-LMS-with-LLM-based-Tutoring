from Importers.common_imports import *
from Importers.common_methods import *
from Database.methods import *


def create_query(conn,course,query,user_id):
    error = insert_query(conn,query,user_id,course)
    if error:
        return error
    return


def answer_query(conn,queryid,answer,user_id):
    return update_answer_to_query(conn,queryid,answer,user_id)


def get_queries(conn,course_id):
    try:
        return select_queries(conn,course_id)
    except Exception as e:
        return None,e


query_map = {
    "create_query": create_query,
    "answer_query": answer_query
}