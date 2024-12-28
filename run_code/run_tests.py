import multiprocessing
import json
from typing import List, Dict
from . import redis_operations
import settings
from pydantic_models import TestCase

redis_client = redis_operations.RedisOperations()


def _execute_function(func, test_case: Dict, result_queue: multiprocessing.Queue):
    """
    executes the function and stores the output in final_result["test_result"] which is a list

    Args:
        func (FunctionType): the function going to get executed.
        args (Tuple): arguments for func
        final_result (Dict): _description_
    """
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


def run_tests(function, test_cases: List[Dict], execution_id: str):
    print("test_cases: List[Dict] = ", test_cases)
    final_result = {'execution_id': execution_id, 'test_result': None}
    result_queue = multiprocessing.Queue()
    processes = {
        multiprocessing.Process(
            target=_execute_function, args=(function, testcase, result_queue)
        ): testcase.get("id")
        for testcase in test_cases
    }
    for process in processes:
        process.start()
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

    final_result["test_result"] = [result_queue.get() for _ in range(result_queue.qsize())]
    print(f"final_result: {final_result}")
    redis_client.set_value(
        key=execution_id, value=json.dumps(final_result), ex=settings.REDIS_EXPIRE_SEC
    )
