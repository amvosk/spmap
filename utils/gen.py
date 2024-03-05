import sched, time
from multiprocessing import Process, Queue, Event


def generate_data(scheduler, stop_event):
    while not stop_event.is_set():
        print("Generating data...")
        # Do something to generate data

if __name__ == '__main__':
    message_queue = Queue()
    stop_event = Event()
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(1, 1, generate_data, (scheduler, stop_event))

    p1 = Process(target=generate_data, args=(scheduler, stop_event))
    p1.start()

    time.sleep(2)
    stop_event.set()

    p1.join()
