import socket
import urllib
import CacheHandler
import traceback
import subprocess
import sys

# Build a simple cache server in python: https://alexanderell.is/posts/simple-cache-server-in-python/

# The mark which lets http server know it is measure client request.
RTT_MEASURE_PATH = '/ping-'


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


def fetch_from_server(url):
    """
    Get header and content by url
    :param url: The url which client request
    :return
    The header and content by url
    """

    q = 'http://' + url

    try:
        print(q)
        response = urllib.urlopen(q)
        # Grab the header and content from the server req
        response_headers = response.info().__str__()
        content = response.read()
        if response.code != 200:
            raise Exception('code != 200')
        print(response.code)
        response_headers = 'HTTP/1.1 200 OK\r\n' + response_headers

        return response_headers, content
    except:
        traceback.print_exc()
        return None


class HttpServer:
    """
    this http server based on a socket waiting  for client to connect and send request.
    To make sure the performance, we created a cache along with this http server.
    When receiving a request from client, this http server will check if there is a cached
    response for this request. If there is, response with the cache.
    If not, it will continue the request the resource from the origin server.
    """
    def __init__(self, origin, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('', port))
        self.origin = origin
        self.cache_handler = CacheHandler.CacheHandler()

    # the method that close the server
    def shutdown(self):
        self.server.close()

    def process_rtt_request(self, path):
        """
        Get result of rtt
        :param path: The path in the request
        :return
        The content according to path
        """
        print('rtt path: ', path)
        client_ip = path[len(RTT_MEASURE_PATH):]
        result = subprocess.check_output(["scamper", "-c", "ping -c 1", "-i", client_ip])

        return result

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
                    print('----------- measure ------------')
                    rtt_rqst = self.process_rtt_request(path)
                    print('rtt', rtt_rqst)
                    conn.sendall(rtt_rqst.encode())
                    conn.close()
                    print('---------- finish measure -------')

                else:
                    print('--------------- GET -------------')
                    data = self.do_GET(path)
                    conn.sendall(data)
                    conn.close()
            except KeyboardInterrupt:
                self.shutdown()
                return
            except Exception:
                print(traceback.format_exc())

    def do_GET(self, path):
        """
        According to situation to process the get request
        :param path: The path in the request
        :return
        The information of rtt
        """
        # if in the cache, return the content in cache
        # else generate http GET request according to the url

        file_from_cache = self.cache_handler.get(path)
        if file_from_cache is not None:
            print('Fetched successfully from cache.')
            response_headers = 'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(file_from_cache)) + '\r\n\r\n'

            return response_headers.encode() + file_from_cache
        else:
            # get the content from origin server and put it into cache
            url = self.origin + ':8080' + path
            print('Not in cache. Fetching from server.')
            headers, file_from_server = fetch_from_server(url)

            if file_from_server is not None:
                self.cache_handler.set(path, file_from_server)
                return (headers + '\r\n').encode() + file_from_server
            else:
                return None


if __name__ == "__main__":
    PORT = int(sys.argv[1])
    ORIGIN = sys.argv[2]
    server = HttpServer(ORIGIN, PORT)
    print('listening...')
    server.serve_forever()

    # run the server: python HttpServer.py 50004 ec2-18-207-254-152.compute-1.amazonaws.com
    # use replica to test: wget ec2-34-238-192-84.compute-1.amazonaws.com:50004/wiki/Main_Page
