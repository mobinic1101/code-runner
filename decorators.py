from fastapi import Response, Request
from fastapi import status
from functools import wraps
import dependencies
from run_code.redis_operations import redis_operations


def prevent_overlapping_process(func):
    """
    Decorator to prevent overlapping processes based on IP address.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable
    """
    
    @wraps(func)
    def wrapper(request: Request, *args, **kwargs):
        # if client's ip address found in the memory we reject the request.
        ip_addr = request.client.host
        result = redis_operations.get_value(ip_addr)
        if result:
            print(f"result of prevent overlapping decorator from redis: {result}")
            return Response(
                content = "there is already a process[%s] running please wait..." % result,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return func(request, *args, **kwargs)       
        
    return wrapper