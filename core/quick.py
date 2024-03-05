# # Import the event manager class
# from event_manager import EventManager
#
# # Create an instance of the event manager
# em = EventManager()
#
# # Define some events
# EVENT_A = "event_a"
# EVENT_B = "event_b"
#
# # Define some event handlers
# def event_a_handler(data):
#     print("Event A triggered with data:", data)
#
# def event_b_handler(data):
#     print("Event B triggered with data:", data)
#
# # Register the event handlers with the event manager
# em.register_handler(EVENT_A, event_a_handler)
# em.register_handler(EVENT_B, event_b_handler)
#
# # Trigger some events
# em.trigger(EVENT_A, "hello") # prints "Event A triggered with data: hello"
# em.trigger(EVENT_B, {"a": 1, "b": 2}) # prints "Event B triggered with data: {'a': 1, 'b': 2}"

import copy
from dataclasses import dataclass, fields


from dataclasses import dataclass, fields

@dataclass
class MyDataClass:
    field1: int
    field2: str

def change_fields(self, new_value):
    for f in fields(self):
        setattr(self, f.name, new_value)

setattr(MyDataClass,'change_all', change_fields)

obj = MyDataClass(1, '2')
obj.change_all(5)
print(obj)