import base64
import sqlite3

from Raft.node import node
from Config.decorators import faculty_access_token_required,student_access_token_required
from Importers.common_imports import *
from protos import Lms_pb2,Lms_pb2_grpc

from Helpers.assignments import  *
# string studentid = 1;
#     string course = 2;
#     string assignment_name = 3;
#     bytes data = 4;
#     string filename = 5;


def generate_data(data):
    buffer = BytesIO()
    buffer.write(data)
    buffer.seek(0)
    chunk_size = 1024 * 1024
    while chunk := buffer.read(chunk_size):
        yield Lms_pb2.GetSubmittedAssignmentsResponse(data=chunk,code="200")


class AssignmentsService(Lms_pb2_grpc.AssignmentsServicer):
    @student_access_token_required
    def submitAssignment(self, request_iterator, context,**kwargs):
        res = None
        try:
            data = b""
            course = None
            filename = None
            assignment_name = None
            student_id = kwargs["userid"]
            for request in request_iterator:
                data += request.data
                course = request.course
                filename = request.filename
                assignment_name = request.assignment_name
            if not data:
                return Lms_pb2.SubmitAssignmentResponse(error="empty file", code="400")
            with sqlite3.connect("lms.db") as conn:
                op = "assignments.submit_assignment"
                args = {
                    "conn":"conn",
                    "course_id":course,
                    "assignment_id":assignment_name,
                    "filename":filename,
                    "data":base64.b64encode(data).decode("utf-8"),
                    "student_id":student_id
                }
                res = node.leader_append_log(op,args)
                if res:
                    error = submit_assignment(conn,student_id,course,assignment_name, data, filename)
                else:
                    return Lms_pb2.UploadCourseMaterialResponse(error="Majority of nodes are down", code="500")
                if error:
                    return Lms_pb2.SubmitAssignmentResponse(error=f"{error}",code="400")
                else:

                    return Lms_pb2.SubmitAssignmentResponse(error="",code="200")


        except Exception as e:
            print(e)
            return Lms_pb2.SubmitAssignmentResponse(error=str(e),code="400")


    @faculty_access_token_required
    def getSubmittedAssignment(self, request, context,**kwargs):
        try:
            aname = request.assignment_name
            course = request.course
            data, error = get_all_assignments(course, aname)
            if error:
                yield Lms_pb2.GetSubmittedAssignmentsResponse(error=f"{error}", code="400")
            for res in generate_data(data):
                yield res
        except Exception as error:
            yield Lms_pb2.GetSubmittedAssignmentsResponse(error=str(error), code="500")




