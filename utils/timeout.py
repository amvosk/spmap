import sys
import time
import multiprocessing
from functools import wraps
import queue


class TimeoutError(Exception):
    pass


# class Target:
#     def __init__(self, function, timeout_exception, exception_message):
#         self.function = function
#         self.key = False
#         self.value = timeout_exception() if exception_message is None else timeout_exception(exception_message)
#
#     def target(self, *args, **kwargs):
#         try:
#             self.value = self.function(*args, **kwargs)
#             self.key = True
#         except:
#             self.value = sys.exc_info()[1]
#
#
# def timeout(seconds=None, timeout_exception=TimeoutError, exception_message=None):
#     def decorate(function):
#         @wraps(function)
#         def wrapper(*args, **kwargs):
#             target = Target(
#                 function=function,
#                 timeout_exception=timeout_exception,
#                 exception_message=exception_message,
#             )
#             # process = multiprocessing.Process(target=target, args=args, kwargs=kwargs)
#             # process = multiprocessing.Process(target=target.target, args=args, kwargs=kwargs)
#             thread = Thread(target=target.target, args=args, kwargs=kwargs)
#             thread.daemon = True
#             thread.start()
#             # thread.join()
#             time.sleep(seconds)
#             # print(target.key, target.value)
#             # if process.is_alive():
#             #     process.terminate()
#             # try:
#             # print(target.key, target.value)
#             # print(target.key, target.value)
#             if target.key:
#                 # raise timeout_exception() if exception_message is None else timeout_exception(exception_message)
#                 return target.value
#             else:
#                 raise target.value
#                 # a = process.start()
#                 # print(a)
#                 # print('start try', args)
#                 # print(q.empty())
#                 # flag, value = q.get(timeout=seconds)
#                 # flag, value = q.get()
#                 # print('!!!!!!!!!!!!!!!', flag, value)
#                 # if not flag:
#                 #     raise value
#                 # return value
#             # except queue.Empty:
#             #     raise timeout_exception() if exception_message is None else timeout_exception(
#             #         exception_message) from None
#             # finally:
#             #     if process.is_alive():
#             #         process.terminate()
#
#         return wrapper
#
#     return decorate


def timeout(seconds=None, return_result=True, timeout_exception=TimeoutError, exception_message=None):
    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            q = multiprocessing.Queue(1)
            args = (q, function) + args
            print(args)
            target_function = targe_full if return_result else target_idle
            print(target_function, function)
            process = multiprocessing.Process(target=target_function, args=args, kwargs=kwargs)
            process.start()
            print('44444444444')
            try:
                flag, value = q.get(timeout=seconds)
                print(flag, value)
                if not flag:
                    raise value
                return value
            except queue.Empty:
                raise timeout_exception() if exception_message is None else timeout_exception(
                    exception_message) from None
            finally:
                if process.is_alive():
                    process.terminate()

        return wrapper

    return decorate


def target_idle(q, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
        q.put((True, True))
    except:
        q.put((False, sys.exc_info()[1]))


def targe_full(q, function, *args, **kwargs):
    try:
        q.put((True, function(*args, **kwargs)))
    except:
        q.put((False, sys.exc_info()[1]))


# @timeout(3)
def mytest(n):
    for i in range(1, n + 1):
        time.sleep(1)
        print("{} seconds have passed".format(i))
    return ['a', 'b']


# def mytest2(n):
#     from pylsl import StreamInlet, resolve_stream
#     streams = resolve_stream('name', 'EBNeuro_BePLusLTM_192.168.171.81')
#     return streams
#     # return ['a', 'b']

if __name__ == '__main__':
    streams = timeout(3)(mytest2)(2)
    print(streams)
    # try:
    #     timeout(3)(mytest)(5)
    # except:
    #     time.sleep(2)
    print('end')
