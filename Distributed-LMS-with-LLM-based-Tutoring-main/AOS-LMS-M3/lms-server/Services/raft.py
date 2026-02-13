from Importers.common_imports import *
from protos import Lms_pb2, Lms_pb2_grpc
from Raft.node import node


class RaftService(Lms_pb2_grpc.RaftServicer):
    def appendEntries(self, request, context):
        try:

            log_message = {
                "term": request.term,
                "leader_id": request.leader_id,
                "prev_log_idx": request.prev_log_idx,
                "prev_log_term": request.prev_log_term,
                "entries": request.entries,
                "leader_commit_idx": request.leader_commit_idx,
            }
            success, term = node.follower_append_entries(log_message)
            return Lms_pb2.AppendEntriesResponse(term=term, success=success)
        except Exception as error:
            print(f"Error in Append Entries : {error}")
            return Lms_pb2.AppendEntriesResponse(success=False,term=request.term)

    def requestVote(self, request, context):
        try:
            request_vote_message = {
                "term": request.term,
                "candidate_id": request.node_id,
                "last_log_idx": request.last_log_idx,
                "last_log_term": request.last_log_term,

            }
            return node.follower_request_vote(request_vote_message)
        except Exception as error:
            print(error)
            return Lms_pb2.RequestVoteResponse(term=request.term, vote_granted=False)

    def getLeader(self, request, context):
        try:
            # Get the current leader information from the node
            leader_info = node.leader_node

            # If leader_node is not set, return an empty or fallback response
            if leader_info is None:
                leader_info = ""

            # Create and return the GetLeaderResponse
            return Lms_pb2.GetLeaderResponse(node_id=leader_info)

        except Exception as error:
            print(error)
            # Return empty node_id in case of an error
            return Lms_pb2.GetLeaderResponse(node_id="")