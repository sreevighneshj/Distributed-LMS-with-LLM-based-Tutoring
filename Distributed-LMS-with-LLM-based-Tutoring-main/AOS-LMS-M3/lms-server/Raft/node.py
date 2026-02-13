import json
import concurrent.futures
import threading
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from protos import Lms_pb2,Lms_pb2_grpc
from Database.methods import gen_uuid
from Importers.common_imports import *
from Importers.common_methods import *
from Config.secrets import settings
from Helpers.assignments import assignments_map
from Helpers.queries import query_map
from Helpers.materials import materials_map

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

def get_random_leader_timeout(node_id):
    random.seed(node_id)
    return random.randint(200, 400)

class MillisecondIntervalTrigger(IntervalTrigger):
    def __init__(self, milliseconds=1000, **kwargs):
        # Convert milliseconds to timedelta
        self.milliseconds = milliseconds
        interval_timedelta = timedelta(milliseconds=milliseconds)
        super().__init__(**kwargs, seconds=interval_timedelta.total_seconds())

    def get_next_fire_time(self, previous_fire_time, now):
        """
        Override the method to account for milliseconds in the interval.
        """
        if previous_fire_time:
            next_fire_time = previous_fire_time + timedelta(milliseconds=self.milliseconds)
            if next_fire_time <= now:
                next_fire_time = now + timedelta(milliseconds=self.milliseconds)
            return next_fire_time
        else:
            return now + timedelta(milliseconds=self.milliseconds)


# Custom scheduler that supports millisecond intervals
class MillisecondScheduler(BackgroundScheduler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_millisecond_job(self, func, milliseconds, **kwargs):
        trigger = MillisecondIntervalTrigger(milliseconds=milliseconds)
        return self.add_job(func, trigger, **kwargs)

class Timer:
    def __init__(self,node_id):
        self.heartbeat_interval = 100
        self.leader_timeout = get_random_leader_timeout(node_id)
        self.scheduler = MillisecondScheduler()
        self.hb_job = self.scheduler.add_millisecond_job(self.heartbeat, milliseconds=self.heartbeat_interval,max_instances=10)
        self.lt_job = self.scheduler.add_millisecond_job(self.leader_timer, milliseconds=self.leader_timeout,max_instances=10)
        self.last_hb_val = 0
        # self.scheduler.add_job()
        # self.next_idx = 0
        # self.last_commited = 0
        # self.term = 1
    # def start(self):

    def heartbeat(self):
        with sqlite3.connect("lms.db") as conn:
            state = node.get_state_info(conn)["state"]
        if state == "L":
            node.leader_append_entries()
    def leader_timer(self):
        with sqlite3.connect("lms.db") as conn:
            state = node.get_state_info(conn)["state"]
        if state != "L":
            hb_val  = node.get_heart_beat_tracker()
            if self.last_hb_val == hb_val:
                node.candidate_request_vote()
            else:
                self.last_hb_val = hb_val
    def start(self):
        print(f"My Leader Timeout is : {self.leader_timeout}")
        self.scheduler.start()
    def stop(self):
        self.scheduler.shutdown()
    def pause(self):
        self.scheduler.pause()
    def resume(self):
        self.scheduler.resume()
    def reset_lt(self):
        self.lt_job.remove()
        self.lt_job = self.scheduler.add_millisecond_job(self.leader_timer, milliseconds=self.leader_timeout, max_instances=5)
    def reset_ht(self):
        self.hb_job.remove()
        self.hb_job = self.scheduler.add_millisecond_job(self.heartbeat, milliseconds=self.heartbeat_interval, max_instances=5)






def apply(operation,args):
    with sqlite3.connect("lms.db") as conn:
        module,func = operation.split('.')
        for k,v in args.items():
            if k == "conn":
                args[k] = conn
        if module == "assignments":
            assignments_map[func](**args)
        elif module == "materials":
            materials_map[func](**args)
        elif module == "queries":
            query_map[func](**args)


def set_nodes():
    with sqlite3.connect("lms.db") as conn:
        cur_node =None
        node_list = []
        query = """SELECT id,host,port FROM node_discovery"""
        cur = conn.cursor()
        cur.execute(query)
        nodes = cur.fetchall()
        for node in nodes:
            node_info = {
                "id":node[0],
                "host":node[1],
                "port":node[2],
            }
            if node_info["id"] == settings.NODE_ID:
                cur_node = node_info
            else:
                node_list.append(node_info)
        return cur_node,node_list

def get_nxt_match_index(nodes,num):
    return {node["id"]:num for node in nodes}

def synchronized_method(lock_name):
    def decorator(method):
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kwargs)
        return wrapper
    return decorator

class Node:
    def __init__(self):
        self.cur_node, self.nodes = set_nodes()
        self.commited_index = 0
        self.last_applied = 0
        self.state = "F"  # Follower by default
        self.leader_node = None
        self.next_index = get_nxt_match_index(self.nodes, 1)
        self.match_index = get_nxt_match_index(self.nodes, 0)
        self.heartbeat_tracker = 0
        self._lock = threading.RLock()


    # ----------- LEADER FUNCTIONS --------------
    def candidate_request_vote(self):
        """
        set state -> C
        term + 1
        -> requestVoteRPC
        wait for majority
        if majority:
            set state -> L
            set leader_node = cur
            initial next_ind
            ini match idx
            last_applied
        no majority:
            set state -> F

        """
        """
            Start an election by requesting votes from other nodes.
            """


        with sqlite3.connect("lms.db") as conn:
            state = self.get_state_info(conn)
            self.set_state("C")
            self.set_term(state["term"] + 1,conn)
            state = self.get_state_info(conn)
            votes_received = 1  # Vote for self
            self.set_voted_for(self.cur_node["id"],conn)
            cur = conn.cursor()
            query = """
            SELECT idx,term FROM raft_logs ORDER By idx DESC LIMIT 1;
            """
            cur.execute(query)
            res = cur.fetchone()
            if not res :
                last_index,last_term = 0,0
            else:
                last_index,last_term = res[0],res[1]
        args = {
            "term": state["term"],
            "node_id": self.cur_node["id"],
            "last_log_idx": last_index,
            "last_log_term": last_term,
        }
        majority = ((len(self.nodes) + 1 )// 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.nodes) + 1) as executor:
            future_vote_requests = {
                executor.submit(self.send_request_vote, node, args): node for node in self.nodes
            }

            for future in concurrent.futures.as_completed(future_vote_requests):
                node = future_vote_requests[future]
                try:
                    success, node_term = future.result()

                    if success:
                        votes_received += 1
                    with sqlite3.connect("lms.db") as conn:
                    # If another node has a higher term, step down as follower
                        if node_term > state["term"]:
                            self.set_term(node_term,conn)
                            self.set_state("F")
                            timer.reset_lt()
                            return False

                        # If the majority votes are received, become the leader
                        if votes_received > majority:
                            self.set_state("L")
                            self.leader_node = self.cur_node["id"]
                            print("Leader elected! I am the LEADER")
                            self.next_index = get_nxt_match_index(self.nodes, last_index + 1)
                            self.match_index = get_nxt_match_index(self.nodes, 0)
                            self.leader_append_entries()
                            return True

                except Exception as exc:
                    # print(f"RequestVote from {node['id']} generated an exception: {exc}")
                    pass

        # No majority, retry election
        timer.reset_lt()
        return False

    def send_request_vote(self, node_info, vote_request):
        """
        Simulates sending a RequestVote RPC to another node.
        Returns whether the node voted for this candidate.
        """
        try:
            with grpc.insecure_channel(f"{node_info['host']}:{node_info['port']}") as channel:
                stub = Lms_pb2_grpc.RaftStub(channel)
                response = stub.requestVote(Lms_pb2.RequestVoteRequest(**vote_request),timeout=1)
                return response.vote_granted, response.term

        except Exception as error:
            # print(f"Error sending RequestVote to {node_info['id']}: {error}")
            return False, vote_request["term"]






    def leader_append_log(self, operation, args):
       try:

           with sqlite3.connect("lms.db") as conn:
               state = self.get_state_info(conn)
               cur = conn.cursor()
               query = """
                      INSERT INTO raft_logs(id, operation, args, term, idx, created_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
                      """
               cur.execute(query, (gen_uuid(), operation, json.dumps(args), state["term"], state["idx"] + 1,))
               conn.commit()
               idx = self.increment_idx(state["idx"],conn)
               cur.close()
               result = self.leader_append_entries()
               if result:
                   self.leader_set_commited_index(idx)
                   self.leader_set_last_applied(idx)
               return idx
       except Exception as error:
           print(error)


    def append_entries_to_node(self, node_info):
        """
        Mocked RPC logic for sending AppendEntries to a follower node.
        Simulates a successful log replication or failure based on random behavior.
        """
        try:
            with sqlite3.connect("lms.db") as conn:
                cur = conn.cursor()
                query = """
                    SELECT idx,term from raft_logs WHERE idx = ? - 1 ORDER BY idx 
                """
                cur.execute(query, (node_info["idx"],))
                res = cur.fetchone()
                if res is None:
                    prev_idx = 0
                    prev_term = 0
                else:
                    prev_idx = res[0]
                    prev_term = res[1]
                query = """
                             SELECT idx,term,operation,args from raft_logs WHERE idx >=?  ORDER BY idx 
                             """
                cur.execute(query, (node_info["idx"],))
                res = cur.fetchall()

                entries = []

                last_idx = None
                for entry in res:

                    fmt_log = {
                        "idx": entry[0],
                        "term": entry[1],
                        "operation": entry[2],
                        "args": entry[3],
                    }
                    """
                    {
                    \"idx\":1,
                    \"term\":1,
                    \"operation\":\"queries.create_query\",
                    \"args\":"{\"conn\": \"conn\", \"course\": \"8d313659-2360-44a2-9ab0-57dbd1ddc201\", \"query\": \"Can I use erlang?\", \"user_id\": \"d53e0c0b-d0a8-4ff7-85c1-fb68030ef577\"}"
                    """
                    last_idx = entry[0]
                    entries.append(fmt_log)

                log = {
                    "term": node_info["term"],
                    "leader_id": node_info["leader_node"],
                    "leader_commit_idx": node_info["commited_index"],
                    "prev_log_idx": prev_idx,
                    "prev_log_term": prev_term,
                    "entries": json.dumps({"entries": entries}),
                }
                try:
                    with grpc.insecure_channel(f"{node_info['host']}:{node_info['port']}") as channel:
                        # Create a stub (client)
                        stub = Lms_pb2_grpc.RaftStub(channel)

                        # Send the AppendEntries request
                        response = stub.appendEntries(Lms_pb2.AppendEntriesRequest(**log),timeout=1)
                    success, term = response.success, response.term
                except Exception as error:

                    return False,None
                if success:
                    if last_idx:
                        self.leader_set_next_index(node_info["id"], last_idx + 1)
                        self.leader_set_match_index(node_info["id"], last_idx)

                    return True,last_idx
                else:

                    if term == node_info["term"]:
                        if prev_idx == 0:
                            self.leader_set_next_index(node_info["id"], 1)

                        else:
                            self.leader_set_next_index(node_info["id"], prev_idx)

                        return True,None

                    elif term > node_info["term"]:
                        self.set_term(term,conn)
                        self.set_state("F")
                        return True,None
                    elif term < node_info["term"]:
                        print("Impossible")

                    return False,None
        except Exception as error:

            return False,None
    def leader_append_entries(self):
        """
        Handles log replication for the leader. Sends AppendEntries RPCs to all followers.
        Returns early if the majority acknowledges.
        """
        try:

            with sqlite3.connect("lms.db") as conn:
                state = self.get_state_info(conn)
            nodes = self.nodes
            acks = 1
            commit = False
            for node in nodes:
                node["term"] = state["term"]
                node["commited_index"] = self.leader_get_commited_index()
                node["leader_node"] = self.leader_node
                node["idx"] = self.leader_get_next_index(node["id"])
            #     success,commit_idx = self.append_entries_to_node(node)
            #     if success:
            #         acks += 1
            #     if acks > ((len(nodes) + 1) // 2):
            #         commit = True
            #         break
            # if commit:
            #     return True  # Log replication succeeded with majority
            # else:
            #     return False


            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_append_entries = {
                    executor.submit(self.append_entries_to_node, node): node for node in nodes
                }

                for future in concurrent.futures.as_completed(future_append_entries):
                    response = future_append_entries[future]
                    try:
                        data, commit_idx = future.result()

                    except Exception as exc:
                        print(f'{response} generated an exception: {exc}')
                    else:
                        if data:  # If log replication succeeded
                            acks += 1
                        else:
                            continue
                        # Check if majority is reached
                        if acks > ((len(nodes) + 1) // 2):
                            commit = True
                            break

                # Shutdown the executor, canceling pending tasks if needed
                executor.shutdown(cancel_futures=True)

            if commit:
                return True  # Log replication succeeded with majority
            else:
                return False
        except Exception as error:
                print(error)

    # ----------- FOLLOWER FUNCTIONS --------------
    def follower_append_entries(self, log_message):
        """
        Handles AppendEntries RPC on the follower side.
        Updates follower's log and commits entries if they pass consistency checks.
        """
        try:

            self.incr_heartbeat_tracker()
            entries = json.loads(log_message["entries"])["entries"]

            with sqlite3.connect("lms.db") as conn:
                state = self.get_state_info(conn)

                # Step down if the leader's term is higher
                if log_message["term"] > state["term"]:
                    self.set_term(log_message["term"],conn)
                    self.state = "F"  # Become follower
                    state = self.get_state_info(conn)
                    timer.reset_lt()
                # Reject the request if the term is outdated
                elif log_message["term"] < state["term"]:
                    print("Term is old")
                    return False, state["term"]
                if not entries and log_message["prev_log_idx"] == 0:

                    return True, log_message["term"]
                # Check if the follower's log contains the previous log entry
                cur = conn.cursor()
                if log_message["prev_log_idx"] != 0:

                    query = "SELECT idx, term FROM raft_logs WHERE idx = ? AND term = ?"
                    cur.execute(query, (log_message["prev_log_idx"], log_message["prev_log_term"]))
                    prev_exists = cur.fetchone()

                    if not prev_exists:
                        print(f"Missing previous entry{log_message['prev_log_term']}:{log_message['prev_log_idx']}")
                        # If the follower's log is inconsistent with the leader's log, return false
                        return False, state["term"]

                """  Handling wrong entries ?"""
                # Append the new entries if the logs match
                idx = state["idx"]
                for entry in entries:
                    cur.execute(
                        "INSERT INTO raft_logs (idx, term, operation, args) VALUES (?, ?, ?, ?) ON CONFLICT(idx,term) DO NOTHING ",
                        (entry["idx"], entry["term"], entry["operation"], entry["args"],)
                    )
                    idx = entry["idx"]
                if idx > state["idx"]:

                    self.set_idx(idx, conn)
                conn.commit()
                # if idx == state["idx"]:
                #     return True, state["term"]
                # Update the follower's commit index and apply the log entries
                commit_idx = self.leader_get_commited_index()
                if log_message["leader_commit_idx"] > commit_idx:
                    commit_idx = min(log_message["leader_commit_idx"], idx)
                    self.apply_committed_entries(commit_idx,conn)

                return True, state["term"]
        except Exception as error:
            # print(f"Error in follower append entries: {error}")
            return False, log_message["term"]

    def apply_committed_entries(self,commit_idx,conn):
        """
        Apply all committed log entries to the state machine.
        """

        cur = conn.cursor()
        query = "SELECT idx,term, operation, args FROM raft_logs WHERE idx <= ? and idx > ?  ORDER BY idx"
        cur.execute(query, (commit_idx, self.leader_get_last_applied(),))
        committed_entries = cur.fetchall()
        for entry in committed_entries:
            operation = entry[2]
            args = json.loads(entry[3])
            apply(operation, args)
            self.leader_set_last_applied(entry[0])
        self.leader_set_commited_index(commit_idx)
        conn.commit()
        cur.close()

    def follower_request_vote(self, request):
        """
        Handles an incoming RequestVote RPC.
        This is the receiver-side logic where a follower responds to a candidate's vote request.

        request: The RequestVote request from the candidate.
        context: gRPC context object.
        """

        try:

            with sqlite3.connect("lms.db") as conn:
                state = self.get_state_info(conn)
                # Step 1: If the candidate's term is less than the follower's term, reject the request
                if request["term"] < state["term"]:
                    return Lms_pb2.RequestVoteResponse(vote_granted=False, term=state["term"])

                # Step 2: If the candidate's term is greater, update the follower's term and reset the state
                if request["term"] > state["term"]:
                    self.set_term(request["term"],conn)
                    self.set_state("F")  # Become a follower in the new term

                # Step 3: Check if follower has already voted in this term
                if state["voted_for"] and state["voted_for"] != request["candidate_id"]:
                    return Lms_pb2.RequestVoteResponse(vote_granted=False, term=state["term"])

                # Step 4: Log consistency check
                # The candidate's log must be at least as up-to-date as the follower's log

                cur = conn.cursor()
                query = """
                            SELECT idx,term FROM raft_logs ORDER By idx DESC LIMIT 1;
                            """
                cur.execute(query)
                res = cur.fetchone()
                if not res:
                    last_index, last_term = 0, 0
                else:
                    last_index, last_term = res[0], res[1]


                if (request["last_log_term"] < last_term or
                        (request["last_log_term"] == last_term and request["last_log_idx"] < last_index)):
                    return Lms_pb2.RequestVoteResponse(vote_granted=False, term=state["term"])

                # Step 5: Grant vote to the candidate
                self.set_voted_for(request["candidate_id"],conn)
                print(f"Granted vote to candidate {request['candidate_id']} for term {request['term']}")
                timer.reset_lt()
                return Lms_pb2.RequestVoteResponse(vote_granted=True, term=request["term"])

        except Exception as error:
            print(f"Error in RequestVote: {error}")
            return Lms_pb2.RequestVoteResponse(vote_granted=False, term=request["term"])


    # ----------- STATE MANAGEMENT FUNCTIONS --------------
    # @synchronized_method("_lock")
    def get_state_info(self,conn):

        cur = conn.cursor()
        query = """
        SELECT  term,idx,voted_for FROM state_info LIMIT 1
        """
        cur.execute(query)
        res = cur.fetchone()
        state_info = {
            "term": res[0],
            "idx": res[1],
            "voted_for": res[2],
            "state": self.state
        }
        cur.close()
        return state_info

    # @synchronized_method("_lock")
    def set_term(self, term,conn):
        cur = conn.cursor()
        query = """
        UPDATE state_info SET term=? , voted_for = NULL
        """
        cur.execute(query, (term,))
        conn.commit()
        cur.close()
        return term

    # @synchronized_method("_lock")
    def set_voted_for(self, voted_for,conn):
        cur = conn.cursor()
        query = """
        UPDATE state_info SET voted_for=?"""
        cur.execute(query, (voted_for,))
        conn.commit()
        cur.close()
        return voted_for

    # @synchronized_method("_lock")
    def set_state(self, state):

        with self._lock:
            self.state = state
        return state

    # @synchronized_method("_lock")
    def increment_idx(self, idx,conn):
        cur = conn.cursor()
        query = """
        UPDATE state_info SET idx=idx+1"""
        cur.execute(query)
        conn.commit()
        cur.close()
        return idx + 1

    def set_idx(self, idx,conn):
        cur = conn.cursor()
        query = """
        UPDATE state_info SET idx=?"""
        cur.execute(query,(idx,))
        cur.close()
        return idx

    # @synchronized_method("_lock")
    def leader_set_next_index(self, node_id, idx):

        self.next_index[node_id] = idx
        return idx

    # @synchronized_method("_lock")
    def leader_set_match_index(self, node_id, idx):

        self.match_index[node_id] = idx
        return idx

    # @synchronized_method("_lock")
    def leader_get_next_index(self, node_id):
        return self.next_index[node_id]

    # @synchronized_method("_lock")
    def leader_get_match_index(self, node_id):
        return self.match_index[node_id]

    # @synchronized_method("_lock")
    def leader_set_last_applied(self, applied):

        self.last_applied = applied
        return applied

    # @synchronized_method("_lock")
    def leader_get_last_applied(self):
        return self.last_applied

    # @synchronized_method("_lock")
    def leader_set_commited_index(self, commited_index):

        self.commited_index = commited_index
        return commited_index
    def incr_heartbeat_tracker(self):

        self.heartbeat_tracker = (self.heartbeat_tracker +1) % 100
    def get_heart_beat_tracker(self):
        return self.heartbeat_tracker
    # @synchronized_method("_lock")
    def leader_get_commited_index(self):
        return self.commited_index

    # @synchronized_method("_lock")
    def get_leader_info(self, id):
        with sqlite3.connect("lms.db") as conn:
            cur = conn.cursor()
            query = """
            SELECT id,host,port FROM node_discovery WHERE id=?
            """
            cur.execute(query, (id,))
            res = cur.fetchone()
            leader_info = {
                "id": res[0],
                "host": res[1],
                "port": res[2]
            }
            cur.close()
            return leader_info

node  = Node()
timer = Timer(node.cur_node["id"])