import grpc

from protos import Lms_pb2,Lms_pb2_grpc
from Helpers.auth import login


class AuthService(Lms_pb2_grpc.AuthServicer):
    def studentLogin(self, request, context):
        try:
            role = "Student"
            token,error = login(request.username, request.password,role)
            if error:
                return Lms_pb2.LoginResponse(error="Invalid email or password",code="401")
            else:
                return Lms_pb2.LoginResponse(token=token,code="200")
        except Exception as e:
            return Lms_pb2.LoginResponse(error="Internal Server Error",code="500")

    def facultyLogin(self, request, context):
        try:
            role = "Instructor"
            token,  error = login(request.username, request.password, role)
            if error:

                return Lms_pb2.LoginResponse(error="Invalid email or password", code="401")
            else:
                return Lms_pb2.LoginResponse(token=token, code="200")
        except Exception as e:
            print(e)
            return Lms_pb2.LoginResponse(error="Internal Server Error", code="500")

