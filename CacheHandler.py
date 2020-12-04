# LRU algo: /cache/data files

import threading
import os
import hashlib
import gzip

MAX_SIZE = 10 * 1024 * 1024


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

    def get(self, path):
        with self.lock:
            file_name = get_hash_path(path)

            if file_name in self.cached_data:
                # move to the head of the list
                self.cached_data.remove(file_name)
                self.cached_data.append(file_name)

                try:
                    file = gzip.open(self.cache_dir + '/' + file_name, 'rb')
                    content = file.read()
                    file.close()
                    return content
                except:
                    self.cached_data.remove(file_name)
                    os.remove(self.cache_dir + '/' + file_name)
                    return None
            else:
                return None

    def set(self, path, data):
        with self.lock:
            file_name = get_hash_path(path)

            if file_name in self.cached_data:
                self.cached_data.remove(file_name)

            elif self.is_full(data):
                discard = self.cached_data.pop(0)
                os.remove(self.cache_dir + '/' + discard)

            file = gzip.open(self.cache_dir + '/' + file_name, 'wb')
            file.write(data.encode('utf-8'))
            file.close()
            self.cached_data.append(file_name)

    def is_full(self, data):
        cache = os.listdir(self.cache_dir)
        total = 0
        for f in cache:
            total += os.path.getsize(self.cache_dir + '/' + f)
        # TODO
        # total += sizeof(data)
        return total >= MAX_SIZE
