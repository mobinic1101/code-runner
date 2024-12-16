import multiprocessing
import json
from typing import List, Dict
import redis_operations
from .. import settings
from ..pydantic_models import TestCase

redis_client = redis_operations.RedisOperations()


def _execute_function(func, test_case: TestCase, final_result: Dict):
    """
    executes the function and stores the output in final_result["test_result"] which is a list

    Args:
        func (FunctionType): _description_
        args (Tuple): _description_
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
    final_result["test_result"].append(test_result)
    print(f"TESTCASE [{test_case.get("id")}] DONE.")


def _timeout_error_message(_id):
    f"""The execution of test case {_id} exceeded the allowed time limit of
{settings.RUN_TESTS_TIMEOUT} seconds;
Please check if the function is taking too long to execute or
if there are any infinite loops in the test case."""


def run_tests(func, test_cases: List[Dict], execution_id: str):
    final_result = {"execution_id": execution_id, "test_result": []}
    processes = {
        multiprocessing.Process(
            target=_execute_function, args=(func, testcase, final_result)
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
            final_result["test_result"].append(process_result)

    redis_client.set_value(
        key=execution_id, value=json.dumps(final_result), ex=settings.REDIS_EXPIRE_SEC
    )
