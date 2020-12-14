import socket
import traceback
import re
import time
import threading
import Queue


class MeasureClient:
    """
     Measure the TTC actively by scamper. Send a dummy request from the client ip used for measurement,
     get TTC using scamper on the server. Find the one having the best TTC.
    """
    def __init__(self, host_names, port):
        # initial the data
        self.probe = ''
        self.hosts = host_names
        self.hosts_rtt = Queue.Queue()  # (host, rtt)
        self.port = port

    def set_probe(self, client_ip):
        #set ip
        self.probe = client_ip

    def set_hosts(self, hosts):
        # set 3 nearest hosts
        self.hosts = hosts

    def generate_request(self):
        # generate the request to http server to get rtt
        path = '/ping-' + self.probe
        rqst = 'GET ' + path + ' HTTP/1.1'
        print(rqst)
        return rqst

    def get_min_rtt_host(self):
        # Get the best host from three nearest hosts
        min = None
        initial_time = 999
        rtt_flag = True

        for item in list(self.hosts_rtt.queue):
            if min is None or item[1] < min[1]:
                min = item

        if min is None:
            return min
        print('min', min)

        if min[1] < initial_time:
            return min[0]
        else:
            for item in list(self.hosts_rtt.queue):
                if item[1] != initial_time:
                    rtt_flag = False
            if rtt_flag:
                return self.hosts[0]

    def get_rtt_help(self, host):
        try:
            print('try--- ', host, self.port)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, self.port))
            s.sendall(self.generate_request().encode())
            while True:
                rtt = s.recv(1024).decode()

                print('raw result ', rtt)
                pattern = re.compile('round-trip min/avg/max/stddev = (.*) ms\n')
                # if there is no rtt response, set it be 999.
                result = pattern.findall(rtt)[0].split('/')[1] if len(pattern.findall(rtt)) > 0 else 999
                print('rtt result ', result)

                self.hosts_rtt.put((host, float(result)))
                break
            s.close()
        except:
            print(self.hosts_rtt)
            traceback.print_exc()
            return

    def get_rtt(self):
        threads = []

        for host in self.hosts:
            t = threading.Thread(target=self.get_rtt_help, args=(host,))
            t.start()
            threads.append(t)
        while threads:
            threads.pop().join()

    def get_best(self):
        print('\n-----------------------------')
        start = time.time()
        self.get_rtt()
        print(time.time() - start)
        print('-----------------------------\n')
        print(list(self.hosts_rtt.queue))
        min_rtt = self.get_min_rtt_host()
        self.hosts_rtt.queue.clear()
        return min_rtt
