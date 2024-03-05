from pylsl import StreamInlet, resolve_stream
# from wrapt_timeout_decorator import *
from timeout import timeout, TimeoutError


# class NoStreamError(ConnectionError):
#     pass
#
# class EmptyStreamError(ConnectionError):
#     pass

# @timeout(1, use_signals=False)
def resolve_stream_timeout(seconds, name, lsl_stream_name):
    timeout(seconds, return_result=False)(resolve_stream)(name, lsl_stream_name)
    return True


class StreamInletTimeout(StreamInlet):
    # @timeout(1, use_signals=False)
    def __init__(self, seconds=None, *args, **kwargs):
        if seconds is not None:
            timeout(seconds, return_result=False)(super().__init__)(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    # @timeout(1, use_signals=False)
    def pull_sample_timeout(self, seconds=None, *args, **kwargs):
        if seconds is not None:
            return timeout(seconds, return_result=True)(self.pull_sample)(*args, **kwargs)
#
#
#
#
# def _connect_lsl(self, config_recorder):
#     try:
#         streams = timeout(3)(resolve_stream)('name', config_recorder.lsl_stream_name)
#         print(streams)
#     except TimeoutError:
#         raise NoStreamError(
#             'No lsl streams with name {} detected'.format(config_recorder.lsl_stream_name)) from None
#     for i, stream in enumerate(streams):
#         try:
#             inlet = timeout(1)(StreamInlet)(stream, config_recorder.fs)
#             _ = timeout(1)(inlet.pull_sample)()
#             return inlet
#         except TimeoutError:
#             print('{} out of {} lsl streams is empty'.format(i + 1, len(streams)))
#     raise EmptyStreamError(
#         'All lsl streams with name {} are empty'.format(config_recorder.lsl_stream_name)) from None
#
#
# class LSL_Inlet:
#     def __init__(self, config_receiver):
#         self.config_receiver = config_receiver
#         self.streams = None
#
#     def connect(self):
#         self.streams = resolve_stream('name', self.config_receiver.lsl_stream_name)
#         try:
#             streams = timeout(3)(resolve_stream)('name', config_receiver.lsl_stream_name)
#             print(streams)
#         except TimeoutError:
#             raise NoStreamError(
#                 'No lsl streams with name {} detected'.format(config_receiver.lsl_stream_name)) from None
#         for i, stream in enumerate(streams):
#             try:
#                 inlet = timeout(1)(StreamInlet)(stream, config_receiver.fs)
#                 _ = timeout(1)(inlet.pull_sample)()
#                 return inlet
#             except TimeoutError:
#                 print('{} out of {} lsl streams is empty'.format(i + 1, len(streams)))
#         raise EmptyStreamError(
#             'All lsl streams with name {} are empty'.format(config_receiver.lsl_stream_name)) from None
#
#     def pull_sample(self):
#         pass
#
#     def pull_sample_timeout(self):
#         pass
