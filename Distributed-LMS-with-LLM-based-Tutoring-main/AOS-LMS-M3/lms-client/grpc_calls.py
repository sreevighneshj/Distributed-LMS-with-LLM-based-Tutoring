import os.path
import threading
import time
import grpc
import Lms_pb2,Lms_pb2_grpc
from imports import grpc_helper
from datetime import datetime

COURSE_ID = "8d313659-2360-44a2-9ab0-57dbd1ddc201"
ASSIGNMENT_ID = "2d8f2298-beac-4a27-b70a-c1da56600993"
LEADER_RETRY_DELAY = 2  # seconds to wait before retrying to fetch the leader
BOOTSTRAP_NODES = [
    {
        "id": "ee1f954b-99ab-48e2-95fd-730e4aec2489",
        "host": "localhost",
        "port": "50052"
    },
    {
        "id": "de3b3357-8c1f-4911-910e-977d2ff02611",
        "host": "localhost",
        "port": "50053"
    },
    {
        "id": "becedead-63a4-48a8-a017-e284cd02d21e",
        "host": "localhost",
        "port": "50054"
    },
{
        "id": "600474f3-0a8f-4ed6-ba56-d9576ddcdb63",
        "host": "localhost",
        "port": "50055"
    }
]


# Function to get the leader id from the bootstrap nodes
def get_leader_id():
    for node in BOOTSTRAP_NODES:
        try:
            server_address = f"{node['host']}:{node['port']}"
            print(f"Trying to connect to bootstrap server: {server_address}")

            with grpc.insecure_channel(server_address) as channel:
                raft_stub = Lms_pb2_grpc.RaftStub(channel)
                response = raft_stub.getLeader(Lms_pb2.GetLeaderRequest(ack=1))  # Call GetLeader RPC

                if response.node_id:
                    print(f"Leader ID found: {response.node_id} (via {server_address})")
                    return response.node_id
                else:
                    print(f"No leader found from {server_address}, trying next...")
        except grpc.RpcError as error:
            print(f"Failed to fetch leader from {server_address}: {error}")

    return None  # If no leader is found or all servers fail


# Function to get leader host and port from the node list based on leader id
def get_leader_host_port(leader_id):
    for node in BOOTSTRAP_NODES:
        if node["id"] == leader_id:
            return node["host"], node["port"]
    return None, None  # If leader ID is not found in the list


# Function to connect to the leader using the host and port, and return the channel
def connect_to_leader(leader_host, leader_port):
    try:
        server_address = f"{leader_host}:{leader_port}"
        channel = grpc.insecure_channel(server_address)

        auth_stub = Lms_pb2_grpc.AuthStub(channel)
        assignment_stub = Lms_pb2_grpc.AssignmentsStub(channel)
        materials_stub = Lms_pb2_grpc.MaterialsStub(channel)
        queries_stub = Lms_pb2_grpc.QueriesStub(channel)
        llm_stub = Lms_pb2_grpc.LlmStub(channel)

        grpc_helper.set_auth_stub(auth_stub)
        grpc_helper.set_assignment_stub(assignment_stub)
        grpc_helper.set_materials_stub(materials_stub)
        grpc_helper.set_queries_stub(queries_stub)
        grpc_helper.set_llm_stub(llm_stub)

        print("Successfully connected to leader:", server_address)
        return channel  # Return the channel for later use
    except grpc.RpcError as error:
        print(f"Failed to connect to leader: {error}")
        return None

def change_server():
    time.sleep(LEADER_RETRY_DELAY)
    leader_id = get_leader_id()

    # Step 2: If leader ID is found, map it to the correct host and port
    if leader_id:
        leader_host, leader_port = get_leader_host_port(leader_id)

        if leader_host and leader_port:
            # Step 3: Attempt to connect to the leader using the host and port
            connect_to_leader(leader_host, leader_port)
def studentLogin(username,password):
    try:
        stub = grpc_helper.auth_stub
        response = stub.studentLogin(Lms_pb2.LoginRequest(username=username,
                                                          password=password))
        if response.code == "200":
            return response.token,None
        else:
            return None,response.error
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        code = rpc_error.code()

        return None,rpc_error

    except Exception as error:
        return None,error

def facultyLogin(username,password):
    try:
        stub = grpc_helper.auth_stub
        response = stub.facultyLogin(Lms_pb2.LoginRequest(username=username,
                                                          password=password))
        if response.code == "200":
            return response.token,None
        else:
            return None,response.error
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        code = rpc_error.code()

        return None, rpc_error

def generate_file_chunks_for_assignment_upload(path,filename,assignment_name):
    block_size = 1024*1024
    with open(path,"rb") as f:
        while chunk := f.read(block_size):
            yield Lms_pb2.SubmitAssignmentRequest(course=COURSE_ID,assignment_name=ASSIGNMENT_ID,data=chunk,filename=filename)


def submitAssignment(assignment_file,assignment_name,filename):
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )

        stub = grpc_helper.assignment_stub
        response = stub.submitAssignment(generate_file_chunks_for_assignment_upload(assignment_file,filename,assignment_name),
                                         metadata=metadata)
        if response.code == "200":
            return None
        else:
            return response.error
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        code = rpc_error.code()

        return rpc_error


def getCourseContents(course,term):
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )

        stub = grpc_helper.materials_stub
        response = stub.getCourseContents(Lms_pb2.GetCourseContentsRequest(course=COURSE_ID,term=term),
                                         metadata=metadata)

        if not response.error:
            return response.data,None
        else:
            return None,response.error
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        code = rpc_error.code()

        return None, rpc_error


def getCourseMaterial(course,term,id):
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )

        stub = grpc_helper.materials_stub
        data = b""
        filename= None
        code = None
        error = None
        for response in stub.getCourseMaterial(Lms_pb2.GetCourseMaterialRequest(course=COURSE_ID,term=term,name=id),
                                         metadata=metadata):
            data += response.data
            filename = response.filename

            error = response.error
        if not error:
            return data,filename,None
        else:
            return None,None,error
    except grpc.RpcError as rpc_error:
        code = rpc_error.code()
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        if code == grpc.StatusCode.UNAUTHENTICATED:
            return None,None,rpc_error.details()
        else:
            return None,None,rpc_error.details()

def getAssignments(course,name):
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )

        stub = grpc_helper.assignment_stub
        data = b""
        code = None
        error = None
        for response in stub.getSubmittedAssignment(Lms_pb2.GetSubmittedAssignmentsRequest(course=COURSE_ID, assignment_name=ASSIGNMENT_ID),
                                          metadata=metadata):
            data += response.data
            code = response.code
            error = response.error
        if not data:
            print(error)
            return None,"No Assignments"
        if code != "200":
            return None,"No Assignments"
        else:
            return data,None

    except grpc.RpcError as rpc_error:
        code = rpc_error.code()
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        if code == grpc.StatusCode.UNAUTHENTICATED:
            return None,rpc_error.details()
        else:
            return None,rpc_error.details()

def generate_file_chunks_for_material_upload(path,filename,material_name):
    block_size = 1024*1024
    with open(path,"rb") as f:
        while chunk := f.read(block_size):
            yield Lms_pb2.UploadCourseMaterialRequest(course=COURSE_ID,term="20241",filename=filename,data=chunk,created=str(datetime.now()),name=material_name)



def uploadMaterial(path,name):
    filename = os.path.split(path)[1]
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )
        stub = grpc_helper.materials_stub
        response = stub.courseMaterialUpload(generate_file_chunks_for_material_upload(path,filename,name),
                                          metadata=metadata)
        if not response.error:
            return None
        else:
            return response.error
    except grpc.RpcError as rpc_error:
        code = rpc_error.code()
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        if code == grpc.StatusCode.UNAUTHENTICATED:
            return rpc_error.details()
        else:
            return rpc_error.details()

def create_query(course, query):
    request = Lms_pb2.CreateQueryRequest(course=COURSE_ID, query=query)
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )
        stub = grpc_helper.queries_stub
        response = stub.createQuery(request,metadata=metadata)
        return response.error
    except grpc.RpcError as e:
        print(f"gRPC failed with {e.code()}: {e.details()}")
        return e.details()

def get_queries(course, term):
    request = Lms_pb2.GetQueriesRequest(course=COURSE_ID, term=term)
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )
        stub = grpc_helper.queries_stub
        response = stub.getQueries(request,metadata=metadata)
        return response.queries,None
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        return None,e.details()
def answer_query( query_id, answer):
    request = Lms_pb2.AnswerQueryRequest(qid=query_id, answer=answer)
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )
        stub = grpc_helper.queries_stub
        response = stub.answerQuery(request,metadata=metadata)
        return response.error
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            change_server()
        print(f"gRPC failed with {e.code()}: {e.details()}")
        return e.details()
def generate_requests():
    session = True
    print("You can ask any queries related to Science and Technology")
    print("Enter 'quit' to stop the chat")
    while session:
        query = input()
        if not query:
           print("Please enter a query")
           continue
        if query == "quit":
            session = False
        else:
            yield Lms_pb2.AskLlmRequest(query=query)
            print(f"You: {query}")
def listen_for_messages(response_iterator):
    for response in response_iterator:
        if response.error:
            print(response.error)
        else:
            print(f"LLM: {response.message}")
def chat_with_phi():
    try:
        metadata = (
            ("authorization", grpc_helper.access_token),
        )
        stub = grpc_helper.llm_stub
        for response in stub.askLlm(generate_requests(), metadata=metadata):
            if response.error:
                print(response.error)
            else:
                print(f"LLM: {response.reply}")

        return None
    except Exception as error:
        return error