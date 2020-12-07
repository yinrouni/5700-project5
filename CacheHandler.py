# LRU algo: /cache/data files ==> LFU

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

        self.cached_data = self.load_cache()  # (hashed_filename, hitcount)

    def load_cache(self):
        with self.lock:
            if os.path.exists(self.cache_dir):
                return map(lambda x: (x, 1), os.listdir(self.cache_dir))
            else:
                os.mkdir(self.cache_dir)
                return []

    def get(self, path):
        with self.lock:
            file_name = get_hash_path(path)

            for item in self.cached_data:

                if file_name == item[0]:
                    # move to the head of the list
                    self.cached_data.append((file_name, item[1] + 1))
                    self.cached_data.remove(item)
                    try:
                        file = gzip.open(self.cache_dir + '/' + file_name, 'rb')
                        content = file.read()
                        file.close()
                        print('cache hit ------ ', self.cached_data)
                        return content
                    except:
                        self.cached_data.remove(item)
                        os.remove(self.cache_dir + '/' + file_name)
                        return None

            return None

    def set(self, path, data):
        with self.lock:
            file_name = get_hash_path(path)

            # if file_name in self.cached_data:
            #     self.cached_data.remove(file_name)
            temp_file = gzip.open(file_name + '.temp', 'wb')
            temp_file.write(data)
            temp_file.close()
            data_size = os.path.getsize(file_name + '.temp')
            if data_size > MAX_SIZE:
                os.remove(file_name + '.temp')
                return
            else:
                while self.is_full(data_size):
                    self.cached_data.sort(key=lambda x: x[1])
                    discard = self.cached_data.pop(0)[0]
                    os.remove(self.cache_dir + '/' + discard)

                os.remove(file_name + '.temp')
                file = gzip.open(self.cache_dir + '/' + file_name, 'wb')
                file.write(data)
                file.close()
                self.cached_data.append((file_name, 1))
                print('cache update ------', self.cached_data)

    def is_full(self, data_size):
        cache = os.listdir(self.cache_dir)
        total = 0
        for f in cache:
            total += os.path.getsize(self.cache_dir + '/' + f)

        total += data_size
        return total >= MAX_SIZE
