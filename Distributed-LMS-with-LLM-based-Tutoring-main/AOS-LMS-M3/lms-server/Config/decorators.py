from functools import wraps
import grpc

from Helpers.auth import generateExpiry
from Config.key_manager import sessionManager
from Importers.common_methods import getTimestamp

def student_access_token_required(f):
    @wraps(f)
    def decorator(self, request_iterator, context,*args, **kwargs):
        id = None
        for k,v in context.invocation_metadata():
            if k == "authorization":
                try:
                    payload = sessionManager.decrypt(v)
                    id,role,expiry = payload.split("|")
                    if role != "Student":
                        context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access Restricted")
                    if expiry < getTimestamp():
                        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Session Expired")
                except Exception as e:
                        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Token")
                kwargs["userid"] = id
                return f(self, request_iterator, context,*args,**kwargs)
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token is Missing")
    return decorator

def faculty_access_token_required(f):
    @wraps(f)
    def decorator(self, request_iterator, context,*args, **kwargs):
        id = None
        for k,v in context.invocation_metadata():
            if k == "authorization":
                try:
                    payload = sessionManager.decrypt(v)
                    id, role, expiry = payload.split("|")
                    if role != "Instructor":
                        context.abort(grpc.StatusCode.PERMISSION_DENIED, "Access Restricted")
                    if expiry < getTimestamp():
                        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Session Expired")
                except Exception as e:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Token")
                kwargs["userid"] = id
                return f(self, request_iterator, context,*args,**kwargs)
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token is Missing")
    return decorator

def any_access_token_required(f):
    @wraps(f)
    def decorator(self, request_iterator, context,*args, **kwargs):
        id = None
        for k,v in context.invocation_metadata():
            if k == "authorization":
                try:
                    payload = sessionManager.decrypt(v)
                    id, _, expiry = payload.split("|")
                    if expiry < getTimestamp():
                        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Session Expired")
                except Exception as e:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid Token")
                kwargs["userid"] = id
                return f(self, request_iterator, context,*args,**kwargs)
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token is Missing")
    return decorator