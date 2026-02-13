from Config.decorators import any_access_token_required
from Importers.common_imports import *
from protos import Lms_pb2,Lms_pb2_grpc


from Helpers.llm import *

class LlmService(Lms_pb2_grpc.LlmServicer):
    @any_access_token_required
    def askLlm(self, request_iterator, context,**kwargs):
        chat_pipeline = Chat()
        for request in request_iterator:
            yield Lms_pb2.AskLlmResponse(reply=chat_pipeline.add_message(request.query),code = "200")




