


class GrpcHelper:
    auth_stub = None
    materials_stub = None
    assignment_stub = None
    access_token = None
    queries_stub =None
    def __init__(self, auth_stub=None, materials_stub=None, assignment_stub=None,queries_stub=None,llm_stub=None):
        self.auth_stub = auth_stub
        self.materials_stub = materials_stub
        self.assignment_stub = assignment_stub
        self.queries_stub = queries_stub
        self.llm_stub = llm_stub
        self.access_token = None
    def set_auth_stub(self,stub):
        self.auth_stub = stub
    def set_materials_stub(self,stub):
        self.materials_stub = stub
    def set_assignment_stub(self,stub):
        self.assignment_stub = stub
    def set_queries_stub(self,stub):
        self.queries_stub = stub
    def set_llm_stub(self,stub):
        self.llm_stub = stub
    def set_access_token(self,access_token):
        self.access_token = access_token

grpc_helper = GrpcHelper()