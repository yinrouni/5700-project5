import socket
import traceback
from urllib.request import Request, urlopen, HTTPError

# Build a simple cache server in python: https://alexanderell.is/posts/simple-cache-server-in-python/

RTT_MEASURE_PATH = '/ping'


def get_request_path(request):
    header = request.split('\r\n\r\n')[0]
    method = header.split('\r\n')[0]
    path = header.split('\r\n')[1] if method == 'GET' else ''
    return path


# TODO handle cache
def fetch_from_server(url):
    url = Request('http://' + url)
    q = Request(url)

    try:
        response = urlopen(q)
        # Grab the header and content from the server req
        response_headers = response.info()
        content = response.read().decode('utf-8')
        return content
    except HTTPError:
        return None


class HttpServer:
    def __init__(self, origin, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        self.origin = origin
        self.cache_handler

    def shutdown(self):
        self.server.close()

    def process_rtt_request(self, request):

        return request

    def serve_forever(self):
        self.server.listen()

        # keep listening
        while True:
            try:
                conn, addr = self.server.accept()
                request = conn.recv(1024).decode()
                print('request: ', request)

                path = get_request_path(request)

                # rtt measure
                if RTT_MEASURE_PATH in path:
                    rtt_rqst = self.process_rtt_request(request)
                    conn.sendall(rtt_rqst.encode())
                    conn.close()

                else:
                    url = self.origin + ':8080' + path
                    data = self.do_GET(url)
                    conn.sendall(data)
                    conn.close()











            except KeyboardInterrupt:
                self.shutdown()
                return
            except Exception:
                print(traceback.format_exc())

    def do_GET(self, url):
        # if in the cache, return the content in cache

        # else generate http GET request according to the url
        if file_from_cache:
            print('Fetched successfully from cache.')
            return file_from_cache
        else:
            print('Not in cache. Fetching from server.')
            file_from_server = fetch_from_server(url)

            if file_from_server:
                save_in_cache(filename, file_from_server)
                return file_from_server
            else:
                return None
