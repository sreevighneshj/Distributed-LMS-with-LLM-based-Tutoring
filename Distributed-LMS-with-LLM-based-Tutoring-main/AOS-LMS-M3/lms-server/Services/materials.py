from fileinput import filename

from Importers.common_imports import *
from protos import Lms_pb2,Lms_pb2_grpc
from Raft.node import node
from Helpers.materials import *
from Config.decorators import faculty_access_token_required,any_access_token_required



def generate_data(name, filename, data):
    chunk_size = 1024 * 1024
    while chunk := data.read(chunk_size):
        yield Lms_pb2.GetCourseMaterialResponse(name=name, filename=filename, data=chunk)


class MaterialsService(Lms_pb2_grpc.MaterialsServicer):
    @faculty_access_token_required
    def courseMaterialUpload(self, request_iterator, context,**kwargs):
        try:
            data = b""
            course=None
            filename= None
            name = None
            req_count = 0
            for request in request_iterator:
                req_count += 1
                data += request.data
                course = request.course
                filename = request.filename
                name = request.name
            if req_count == 0:
                return Lms_pb2.UploadCourseMaterialResponse(size="0", code="200")
            with sqlite3.connect("lms.db") as conn:
                op = "materials.material_upload"
                args = {
                    "conn": "conn",
                    "course_id": course,
                    "filename": filename,
                    "data": data,
                    "name": name
                }

                res = node.leader_append_log(op, args)
                if res:
                    result = upload(conn,course, data,filename,name)
                else:
                    return Lms_pb2.UploadCourseMaterialResponse(error="Majority of nodes are down", code="500")

            if result:
                return Lms_pb2.UploadCourseMaterialResponse(error=f"{result}",code="400")
            else:
                return Lms_pb2.UploadCourseMaterialResponse(size=str(sys.getsizeof(data)),code="200")

        except Exception as e:
            return Lms_pb2.UploadCourseMaterialResponse(error=str(e),code="500")
    @any_access_token_required
    def getCourseContents(self, request, context,**kwargs):
        course = request.course
        with sqlite3.connect('lms.db') as conn:
            list_materials,error= get_course_contents(conn,course)
        if error:
            return Lms_pb2.GetCourseContentsResponse(course=course,error=error)
        else:
            return Lms_pb2.GetCourseContentsResponse(course=course,data=json.dumps(list_materials))

    @any_access_token_required
    def getCourseMaterial(self, request, context,**kwargs):
        try:
            course = request.course
            name = request.name
            with sqlite3.connect('lms.db') as conn:
                data,name,filename,error = get_course_material(conn, course,name)
            if error:
                yield Lms_pb2.GetCourseMaterialResponse(error=error)
            else:
                for res in generate_data(name, filename, data):
                    yield res
        except Exception as error:
            print(error)
            yield Lms_pb2.GetCourseMaterialResponse(error=str(error))




