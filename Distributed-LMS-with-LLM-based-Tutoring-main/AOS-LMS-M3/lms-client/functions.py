import hashlib
import json
import os
import grpc_calls
from grpc_calls import answer_query, chat_with_phi

from imports import grpc_helper
from menu import *


def some_func():
    pass

def hash_this(obj):
    return hashlib.sha256(obj.encode('utf-8')).hexdigest()

def print_error(error):
    print(f"ERROR:   {error}")



def student_login():
    username =input('Username: ') # "abc@gmail.com"
    password = input('Password: ')   #"qwerty00"
    hashed_pwd = hash_this(password)
    token,error = grpc_calls.studentLogin(username, hashed_pwd)
    if error:
        print_error(error)
        return None,False
    else:
        grpc_helper.set_access_token(token)
        return {"options":student_login_options, "actions":student_login_action, "head":"Options for student"},False

def faculty_login():
    username = input('Username: ')  # "dbc@gmail.com"
    password = input('Password: ')  # "qwerty00"
    hashed_pwd = hash_this(password)
    token,error = grpc_calls.facultyLogin(username, hashed_pwd)
    if error:
        print_error(error)
        return None,False
    else:
        print(token)
        grpc_helper.set_access_token(token)
        return {"options":faculty_login_options, "actions":faculty_login_action, "head":"Options for faculty"},False

def logout():
    grpc_helper.set_access_token(None)
    return None,False


main_menu_action = {
    1:student_login,
    2:faculty_login,
    3:logout,
}


main_menu_options = (
    (1,"Student Login"),
    (2,"Faculty Login"),
    (3,"Logout"),
)


def submit_assignment():
    assignment_name = input('Name of the assignmnent: ')
    path_to_file = input('Path to the assignment file: ')
    if not os.path.exists(path_to_file):
        print_error("Path doesn't exist")
        return None,False
    filename = os.path.split(path_to_file)[1]
    print(filename)
    error = grpc_calls.submitAssignment(path_to_file, assignment_name,filename)
    if error:
        print_error(error)
        return None,False
    else:
        print("Assignment Submitted")
        return None,False

def get_course_contents():
    course= "AOS"
    term = "202401"
    return grpc_calls.getCourseContents(course,term)


def get_material(id):
    course = "AOS"
    term = "20241"
    data,filename,error = grpc_calls.getCourseMaterial(course,term,id)

    if error:
        print_error(error)
        return
    else:
        with open(os.path.join(os.getcwd(),"Downloads",filename),"wb") as f:
            f.write(data)
        print("Material Downloaded")



def course_contents_view():
    contents,error = get_course_contents()
    if not contents:
        print_error("No Materials to display")
        return None,False
    contents_json = json.loads(contents)
    contents = contents_json.get("contents")
    if not contents:
        print_error("No Materials to display")
        return None, False

    if  error:
        print_error(error)
        return None,False
    contentMap = {}
    for i in range(len(contents)):
        contentMap[i+1] = contents[i]
        print(f"{i+1}. {contents[i]["name"]}")
    opted = int(input("To download enter the number associated.Otherwise Enter 0 to go back: "))
    if opted == 0:
        return None,False
    else:
        get_material(contentMap[opted]["id"])
        return None,False

def getStudentQueries():
    course = "AOS"
    term = "20241"
    result,error = grpc_calls.get_queries(course, term)
    if error:
        return None,False
    jRes = json.loads(result)
    queryList = jRes.get("q")
    queryMap = {}
    if queryList:
        print("Fetched queries:")
        for q in range(len(queryList)):
            if queryList[q]['reply']:
                queryMap[q + 1] = queryList[q]["id"]
                print(f"[{q + 1}] [{queryList[q]['posted_by']}] --> {queryList[q]['query_text']}")
                print(f"[{queryList[q]['replied_by']}] --> {queryList[q]['reply']}")
                print("-----------------------------")
            else:
                queryMap[q + 1] = queryList[q]["id"]
                print(f"[{q + 1}] [{queryList[q]['posted_by']}] --> {queryList[q]['query_text']}")
                print("Ans:")
                print("-----------------------------")

        return None,False
    else:
        print("Failed to fetch queries.")
        return None,False

def create_query():
    course = "AOS"
    query = input("Enter the query to create: ")
    error = grpc_calls.create_query(course, query)
    if not error:
        print("Query created successfully!")

    else:
        print("Failed to create query.")
    return None,False


def chat_with_llm():
    error = chat_with_phi()
    if error:
        print_error(error)
    return None,False

student_login_options = (
    (1,"Course Contents"),
    (2,"Submit Assignments"),
    (3,"Get Queries"),
    (4,"Create Query"),
    (5,"Chat with LLM")

)

student_login_action = {
    1:course_contents_view,
    2:submit_assignment,
    3:getStudentQueries,
    4:create_query,
    5:chat_with_llm
}


def get_assignments():
    print("Downloading all assignments...")
    name = "Assignment 1"
    course = "AOS"
    file_data,error = grpc_calls.getAssignments(course,name)
    if error:
        print_error(error)
        return None,False
    path = os.path.join(os.getcwd(),"Downloads", course, name)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path,f"{name}.zip"),"wb") as f:
        f.write(file_data)

    print(f"Assignments Downloaded : {name}.zip")
    return None,False

def upload_materials():
    material_name = input('Name of the material: ')
    path_to_file = input('Path to the file: ')
    if not os.path.exists(path_to_file):
        print_error("Path doesn't exist")
        return None, False
    error = grpc_calls.uploadMaterial(path_to_file, material_name)
    if error:
        print_error(error)
        return None, False
    else:
        print("Material Uploaded")
        return None, False


def getFacultyQueries():
    course = "AOS"
    term = "20241"
    result,error = grpc_calls.get_queries(course, term)
    if error:
        return None,False
    jRes = json.loads(result)
    queryList = jRes.get("q")
    queryMap = {}
    if queryList:
        print("Fetched queries:")
        for q in range(len(queryList)):
            if queryList[q]['reply']:
                queryMap[q+1]= queryList[q]["id"]
                print(f"[{q+1}] [{queryList[q]['posted_by']}] --> {queryList[q]['query_text']}")
                print(f"[{queryList[q]['replied_by']}] --> {queryList[q]['reply']}")
                print("-----------------------------")
            else:
                queryMap[q + 1] = queryList[q]["id"]
                print(f"[{q + 1}] [{queryList[q]['posted_by']}] --> {queryList[q]['query_text']}")
                print("Ans:")
                print("-----------------------------")


        opt = int(input("Enter the corresponding number to answer the query . Otherwise enter 0 to go back: "))
        if opt == 0:
            return None,False
        else:
            id = queryMap.get(opt)
            if not id:
                print_error("Invalid Option")
            ans = input("Enter the answer: ")
            error = answer_query(id,ans)
            if error:
                print_error(error)
                return None,False
            print("Query is answered")
            return None,False
    else:
        print("Failed to fetch queries.")
        return None,False

def chat_with_llm():
    error = chat_with_phi()
    print_error(error)
    return None,False

faculty_login_options = (

    (1,"Course Contents"),
    (2,"Get Assignments"),
    (3,"Upload Material"),
    (4,"Get Queries"),
    (5,"Chat with LLM")


)
faculty_login_action = {
    1:course_contents_view,
    2:get_assignments,
    3:upload_materials,
    4:getFacultyQueries,
    5:chat_with_llm
}