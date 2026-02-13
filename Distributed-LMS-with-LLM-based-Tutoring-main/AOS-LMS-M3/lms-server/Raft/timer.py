#
# from Importers.common_imports import *
# from Importers.common_methods import *
# from Raft.node import node
# def get_random_leader_timeout(node_id):
#     random.seed(node_id)
#     return random.randint(6000, 8000)
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.interval import IntervalTrigger
# from datetime import datetime, timedelta
#
#
# class MillisecondIntervalTrigger(IntervalTrigger):
#     def __init__(self, milliseconds=1000, **kwargs):
#         # Convert milliseconds to timedelta
#         self.milliseconds = milliseconds
#         interval_timedelta = timedelta(milliseconds=milliseconds)
#         super().__init__(**kwargs, seconds=interval_timedelta.total_seconds())
#
#     def get_next_fire_time(self, previous_fire_time, now):
#         """
#         Override the method to account for milliseconds in the interval.
#         """
#         if previous_fire_time:
#             next_fire_time = previous_fire_time + timedelta(milliseconds=self.milliseconds)
#             if next_fire_time <= now:
#                 next_fire_time = now + timedelta(milliseconds=self.milliseconds)
#             return next_fire_time
#         else:
#             return now + timedelta(milliseconds=self.milliseconds)
#
#
# # Custom scheduler that supports millisecond intervals
# class MillisecondScheduler(BackgroundScheduler):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#     def add_millisecond_job(self, func, milliseconds, **kwargs):
#         trigger = MillisecondIntervalTrigger(milliseconds=milliseconds)
#         self.add_job(func, trigger, **kwargs)
#
# class Timer:
#     def __init__(self,node_id):
#         self.heartbeat_interval = 5000
#         self.leader_timeout = get_random_leader_timeout(node_id)
#         self.scheduler = MillisecondScheduler()
#         self.scheduler.add_millisecond_job(self.heartbeat, milliseconds=self.heartbeat_interval,max_instances=5,job_id="hb")
#         self.scheduler.add_millisecond_job(self.leader_timeout, milliseconds=self.leader_timeout,max_instances=5,job_id="lt")
#         # self.scheduler.add_job()
#         # self.next_idx = 0
#         # self.last_commited = 0
#         # self.term = 1
#     # def start(self):
#
#     def heartbeat(self):
#         if node.get_state_info()["state"] == "L":
#             print("here")
#             node.leader_append_entries()
#     def leader_timeout(self):
#         if node.get_state_info()["state"] != "L":
#             if not node.get_heart_beat_tracker():
#                 node.candidate_request_vote()
#             else:
#                 node.set_heart_beat_tracker(state=False)
#     def start(self):
#         print("here1")
#         self.scheduler.start()
#     def stop(self):
#         self.scheduler.shutdown()
#     def pause(self):
#         self.scheduler.pause()
#     def resume(self):
#         self.scheduler.resume()
#     def reset_lt(self):
#         self.scheduler.remove_job(job_id="lt")
#         self.scheduler.add_millisecond_job(self.leader_timeout, milliseconds=self.leader_timeout, max_instances=5,
#                                            job_id="lt")
#
#
#
#
# timer = Timer(node.cur_node["id"])
