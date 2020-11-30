# LRU algo: /cache/data files

import threading
import os
import hashlib

MAX_SIZE = 10

def get_hash_path(path):
    m = hashlib.md5()
    m.update(path)
    return m.hexdigest()


class CacheHandler:

    def __init__(self):

        self.lock = threading.Lock()
        self.cache_dir = 'cache'

        self.cached_data = self.load_cache()

    def load_cache(self):
        with self.lock:
            if os.path.exists(self.cache_dir):
                return os.listdir(self.cache_dir)
            else:
                os.mkdir(self.cache_dir)
                return []

    def search(self, path):
        with self.lock:
            file_name = get_hash_path(path)

            if file_name in self.cached_data:





