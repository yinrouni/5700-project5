import socket
import traceback
import urllib
import CacheHandler
import traceback

# Build a simple cache server in python: https://alexanderell.is/posts/simple-cache-server-in-python/

RTT_MEASURE_PATH = '/ping'


def get_request_path(request):
    header = request.split('\r\n\r\n')[0]
    print('header ---- ', header)
    start = header.split('\r\n')[0].split(' ')
    print('start ----', start)
    method = start[0]
    print('method ----', method)
    path = start[1] if method == 'GET' else ''
    print(path)
    return path


# TODO handle cache
def fetch_from_server(url):
    q = 'http://' + url

    try:
        print(q)
        response = urllib.urlopen(q)
        # Grab the header and content from the server req
        response_headers = response.info()

        content = response.read().decode('utf-8')

        #print(content)
        return content
    except:
        traceback.print_exc()
        return None


class HttpServer:
    def __init__(self, origin, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        # print(self.server.getsockname())
        self.origin = origin
        self.cache_handler = CacheHandler.CacheHandler()

    def shutdown(self):
        self.server.close()

    def process_rtt_request(self, request):

        return request

    def serve_forever(self):
        self.server.listen(1)
        print('listened')

        # keep listening
        while True:
            try:
                conn, addr = self.server.accept()
                print('accepted')
                request = conn.recv(1024).decode()
                print('request: ', request)

                path = get_request_path(request)

                # rtt measure
                if RTT_MEASURE_PATH in path:
                    rtt_rqst = self.process_rtt_request(request)
                    conn.sendall(rtt_rqst.encode())
                    conn.close()

                else:
                    data = self.do_GET(path)
                    conn.sendall(data)
                    conn.close()
            except KeyboardInterrupt:
                self.shutdown()
                return
            except Exception:
                print(traceback.format_exc())

    def do_GET(self, path):
        # if in the cache, return the content in cache

        # else generate http GET request according to the url
        file_from_cache = self.cache_handler.get(path)
        if file_from_cache is not None:
            print('Fetched successfully from cache.')
            # print(file_from_cache)
            return file_from_cache
        else:
            url = self.origin + ':8080' + path
            print('Not in cache. Fetching from server.')
            file_from_server = fetch_from_server(url)

            if file_from_server is not None:
                self.cache_handler.set(path, file_from_server)
                return file_from_server.encode('utf-8')
            else:
                return None

if __name__ == "__main__":
    server = HttpServer('ec2-18-207-254-152.compute-1.amazonaws.com', 40004)
    print('listening...')
    server.serve_forever()