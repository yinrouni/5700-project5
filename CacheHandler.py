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
                # move to the head of the list
                self.cached_data.remove(file_name)
                self.cached_data.append(file_name)

                try:
                    file = open(self.cache_dir + '/' + file_name, 'rb')
                    content = file.read()
                    file.close()
                    return content
                except:
                    self.cached_data.remove(file_name)
                    os.remove(self.cache_dir + '/' + file_name)
                    return -1
            else:
                return -1






