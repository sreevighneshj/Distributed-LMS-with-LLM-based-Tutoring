from Importers.common_imports import *
from protos import Lms_pb2,Lms_pb2_grpc
from Config.decorators import student_access_token_required,faculty_access_token_required,any_access_token_required
from Helpers.queries import  *
from Raft.node import node

class QueryService(Lms_pb2_grpc.QueriesServicer):
    @student_access_token_required
    def createQuery(self,request,context,**kwargs):
        try:
            course = request.course
            query = request.query
            with sqlite3.connect("lms.db") as conn:
                op = "queries.create_query"
                args = {
                    "conn": "conn",
                    "course": course,
                    "query": query,
                    "user_id": kwargs["userid"],
                }
                # conn, queryid, answer, user_id
                res = node.leader_append_log(op, args)
                if res:
                    error = create_query(conn,course,query,kwargs["userid"])
                else:
                    return Lms_pb2.UploadCourseMaterialResponse(error="Majority of nodes are down", code="500")

            if error:
                return Lms_pb2.CreateQueryResponse(error=f"{error}",code="400")
            else:
                return Lms_pb2.CreateQueryResponse(error="",code="200")
        except Exception as e:
            print(e)
            return Lms_pb2.CreateQueryResponse(error=str(e),code="400")
    @any_access_token_required
    def getQueries(self,request,context,**kwargs):
        try:
            course = request.course
            with sqlite3.connect("lms.db") as conn:
                queries,error = get_queries(conn,course)
            if error:
                return Lms_pb2.GetQueriesResponse(error=f"{error}",code="400")
            else:
                return Lms_pb2.GetQueriesResponse(error="",code="200",queries=json.dumps({"q":queries}))
        except Exception as e:
            print(e)
            return Lms_pb2.GetQueriesResponse(error=str(e),code="400")
    @faculty_access_token_required
    def answerQuery(self,request,context,**kwargs):
        try:
            ans = request.answer
            qid = request.qid
            with sqlite3.connect("lms.db") as conn:
                op = "queries.answer_query"
                args = {
                    "conn": "conn",
                    "queryid": qid,
                    "answer": ans,
                    "user_id": kwargs["userid"],
                }

                res = node.leader_append_log(op, args)
                if not res:
                    return Lms_pb2.UploadCourseMaterialResponse(error="Majority of nodes are down", code="500")
                error = answer_query(conn,qid,ans,kwargs["userid"])
            if error:
                return Lms_pb2.AnswerQueryResponse(error=f"{error}",code="400")
            else:
                return Lms_pb2.AnswerQueryResponse(error="",code="200")
        except Exception as e:
            print(e)
            return Lms_pb2.AnswerQueryResponse(error=str(e),code="400")