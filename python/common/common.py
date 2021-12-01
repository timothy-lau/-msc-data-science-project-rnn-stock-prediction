import os
import pickle


def read_latest_file(dir, file_prefix):
    return dir + '/' + max([file for file in os.listdir(dir) if file_prefix in file])

def write_pickle(file_path, data):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def read_pickle(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)