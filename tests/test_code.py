import time
from multiprocessing import Queue


numbers = Queue()
if not numbers.empty():
    message = numbers.get(block=True)
    print(message)

# for i in range (0,10):
#     numbers.put(i)

# time.sleep(1)
# if numbers.qsize()>0 and numbers.empty():
#     print("BUG?!")
