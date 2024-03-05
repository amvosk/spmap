class EventManager:
    def __init__(self):
        self.handlers = {}

    def register_event(self, event):
        if event not in self.handlers:
            self.handlers[event] = []

    def register_handler(self, event, handler):
        if event not in self.handlers:
            self.handlers[event] = []
        self.handlers[event].append(handler)

    def unregister_handler(self, event, handler):
        if event in self.handlers:
            self.handlers[event].remove(handler)

    def trigger(self, event, data=None):
        if event in self.handlers:
            print()
            for handler in self.handlers[event]:
                print(event, handler.__name__)
                handler(data)