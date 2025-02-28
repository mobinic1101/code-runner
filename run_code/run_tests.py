import multiprocessing
import json
import dill
from typing import List, Dict
from . import redis_operations
import settings
from pydantic_models import TestCase

redis_client = redis_operations.RedisOperations()


def _execute_function(
    b_func: bytes, test_case: Dict, result_queue: multiprocessing.Queue
):
    """
    executes the function and stores the output in result_queue

    Args:
        b_func (bytes): the pickled version of the function going to get deserialized and executed.
        args (Tuple): arguments for func
        result_queue (multiprocessing.Queue): a global queue used to store the output of the func.
    """
    func = dill.loads(b_func)

    test_result = {
        "id": test_case.get("id"),
        "output": None,
        "error": None,
        "error_message": None,
    }
    try:
        output = func(*test_case.get("input"))
        test_result["output"] = output
    except Exception as e:
        test_result["error"] = "ExecutionError"
        test_result["error_message"] = str(e)
    result_queue.put(test_result)
    print(f"TESTCASE [{test_case.get("id")}] DONE.")


def _timeout_error_message(_id):
    return f"""The execution of test case {_id} exceeded the allowed time limit of
{settings.RUN_TESTS_TIMEOUT} seconds;
Please check if the function is taking too long to execute or
if there are any infinite loops in the test case."""


def run_tests(function, test_cases: List[Dict], execution_id: str, userid: str):
    """runs a list of testcases on a function in parallel

    Args:
        function (_type_): function to be executed
        test_cases (List[Dict]): list of testcases to be executed over the function
            example of a single testcase: {'id': 1, 'input': (1, 2), 'expected': 3}
        execution_id (str): a unique id for the execution
        userid (str): unique user id (it is used for prevent overlapping process
        like a rate limiter so they cant submit another process if they already 
        have one processing and it can be their 
        session id, authentication token, or their userid(from database))
    """
    print("test_cases: List[Dict] = ", test_cases)
    final_result = {"execution_id": execution_id, "test_result": None}
    result_queue = multiprocessing.Queue()

    # creating processes
    processes: Dict[multiprocessing.Process] = {}
    for testcase in test_cases:
        process = multiprocessing.Process(
            target=_execute_function,
            args=(dill.dumps(function), testcase, result_queue),
        )
        process.start()
        processes[process] = testcase.get("id")

    # wait for processes
    for process in processes:
        process.join(timeout=settings.RUN_TESTS_TIMEOUT)
        if process.is_alive():
            process.terminate()
            process_result = {
                "id": processes[process],
                "output": None,
                "error": "TimeoutError",
                "error_message": _timeout_error_message(processes.get(process)),
            }
            result_queue.put(process_result)

    final_result["test_result"] = [
        result_queue.get() for _ in range(result_queue.qsize())
    ]
    print(f"final_result: {final_result}")
    redis_client.set_value(
        key=execution_id, value=json.dumps(final_result), ex=settings.REDIS_EXPIRE_SEC
    )

    print("received ip addr: {}".format(userid))
    redis_client.set_value(key=str(userid), value=str(execution_id), ex=settings.REDIS_EXPIRE_SEC)
