import base64

from Importers.common_imports import *
from Importers.common_methods import *
from Database.methods import *




def map_dir_contents(folder_path):
    file_dict = {}
    for filename in os.listdir(folder_path):
        if filename == "metadata.json":
            continue
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as file:  # Open the file in binary mode
                file_dict[filename] = file.read()  # Store file content as bytes
    return file_dict


def add_file(path,filename,data):
    if isinstance(data,str):
        data = base64.b64decode(data.encode())
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, f"{filename}"), 'wb') as f:
            f.write(data)
    except Exception as e:
        return e

def create_assignment(conn,name,due_date,description,course_id):
    try:
        error = insert_assignment(conn,name,due_date,description,course_id)
        return error
    except Exception as e:
        return e


def get_assignments(conn,course):
   return select_assignments(conn,course)


def submit_assignment(conn,student_id,course_id,assignment_id,data,filename):
    try:
        new_filename = f"{student_id}-{filename}"
        error = insert_assignment_submission(conn,assignment_id,student_id,new_filename)
        if error:
            return error
        path = os.path.join(os.getcwd(),"Resources",course_id,assignment_id)
        error = add_file(path,new_filename,data)
        if error:
            conn.rollback()
            return error
        conn.commit()
    except Exception as e:
        return e

def get_all_assignments(course,assignment_name):
    try:
        path = os.path.join(os.getcwd(),"Resources",course,assignment_name)
        if not os.path.exists(path):
            return None,"Assignment Not Found"
        data = zip_files_in_directory(path)
        return data,None

    except Exception as error:
        return None,error


assignments_map = {
    "submit_assignment":submit_assignment,
    "create_assignment":create_assignment
}