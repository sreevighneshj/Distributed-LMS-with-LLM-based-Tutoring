from Database.creation_scripts import create_everything, create_assignment_submissions
from Helpers.assignments import create_assignment, submit_assignment
from Importers.common_imports import *
from Services.auth import *
from Raft.node import timer
from Config.key_manager import sessionManager
from Services.llm import LlmService
from Services.materials import MaterialsService
from Services.assignments import AssignmentsService
from Services.queries import QueryService
from Services.raft import RaftService
# class Students(BaseModel):
#     emailId : str
#     studentId : str
#     name : str
#     courses : List[str]
#
#
# class Course(BaseModel):
#     Id : str
#     courseName :  str
#     facultyId : str
#
#
#
#
# class Faculty(BaseModel):
#     emailId : str
#     facultyId : str
#     name : str
#     courses : List[str]
#
# def generateKey(payload):
#     return sessionManager.encrypt(payload)
#
#
# def register():
#     students_db = [{
#         "email": "",
#         "studentId": "",
#         "name": "",
#         "courses": ["AOS", "SEM"],
#         "session_id":"",
#         "session_expiry":""
#
#     }]
#     faculty_db = [
#         {
#             "emailId":"",
#             "facultyId":"",
#             "name":"",
#             "courses":["AOS", "SEM"],
#         }
#     ]
#     courses_db = [
#         {
#             "Id":"",
#             "courseName":"",
#             "facultyId":""
#         }
#     ]

# with open("README.md", "rb") as fh:
#     data = fh.read()
# upload("AOS",data,"20241","trial.md")
def serve():
    port = "50052"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    Lms_pb2_grpc.add_AuthServicer_to_server(AuthService(), server)
    Lms_pb2_grpc.add_MaterialsServicer_to_server(MaterialsService(), server)
    Lms_pb2_grpc.add_AssignmentsServicer_to_server(AssignmentsService(), server)
    Lms_pb2_grpc.add_QueriesServicer_to_server(QueryService(), server)
    Lms_pb2_grpc.add_LlmServicer_to_server(LlmService(), server)
    Lms_pb2_grpc.add_RaftServicer_to_server(RaftService(),server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    timer.start()
    server.wait_for_termination()

if __name__ == '__main__':
    create_everything()
    serve()

