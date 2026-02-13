from Importers.common_imports import *
from Importers.common_methods import *
from Database.methods import *

def add_file(path,filename,data):
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, f"{filename}"), 'wb') as f:
            f.write(data)
    except Exception as e:
        return e




def upload(conn,course_id,data,filename,name):
    try:
        path = os.path.join(os.getcwd(),"Resources",course_id)
        # if  os.path.exists(os.path.join(path,filename)):
        #     return "File already exists"
        error = add_material(conn,course_id,name,filename)
        if error:
            conn.rollback()
            return error
        error = add_file(path,filename,data)
        if error:
            conn.rollback()
            return error
        conn.commit()
    except Exception as e:
        return e

# def get_material(name,path):
#     try:
#         buffer = None
#         if not os.path.exists(path):
#             return None,None, "Material Not Found"
#         with open(os.path.join(path, "metadata.json"), 'r') as f:
#             metadata = json.load(f)
#         if name not in metadata["_index"]:
#             return None,None, "Material Not Found"
#         filename = metadata["_data"][name]
#         if os.path.exists(os.path.join(path,filename)):
#             buffer = BytesIO()
#             with open(os.path.join(path,filename), "rb") as f:
#                 buffer.write(f.read())
#                 buffer.seek(0)
#         return buffer,filename,None
#     except Exception as e:
#         print(e)

# def get_required_material(course_name,term,name):
#     try:
#
#         path = os.path.join(os.getcwd(),"Resources",term,course_name)
#         return get_material(name,path)
#
#     except Exception as e:
#         return e

def get_course_contents(conn,course_name):
    try:
        contents,error = get_course_materials(conn,course_name)
        if contents:
            return {"contents":[{"id":r[0],"name":r[1],"file":r[2]} for r in contents]},error
        else:
            return {"contents":[]},error
    except Exception as error:
        return None,error


def get_course_material(conn,course,id):
    io =BytesIO()
    try:
        material,error = get_material(conn,id)
        if not material:
            return None, None, None, "Material not found"
        path = os.path.join(os.getcwd(),"Resources",material[2],material[1])
        if not os.path.exists(path):
            return None,None,None,"File not found"
        with open(path,'rb') as f:
            data = f.read()
            io.write(data)
            io.seek(0)
        return io,material[0],material[1],error

    except Exception as error:
        print(error)
        return None,None,None,error



materials_map = {
    "upload_material":upload,
}