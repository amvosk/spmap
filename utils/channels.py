
import sys
sys.path.insert(0, '../utils/')
import json

def create_default_channel_names(n_channels):
    channel_names = [str(i+1) for i in range(n_channels)]
    return channel_names



if __name__ == '__main__':
    n_channels = 20
    channel_names = create_default_channel_names(n_channels)
