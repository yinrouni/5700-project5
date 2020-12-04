import socket
import traceback
import re


class MeasureClient:
    def __init__(self, client_ip, host_names, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.probe = client_ip
        self.hosts = host_names
        self.hosts_rtt = []  # (host, rtt)
        self.port = port

    def generate_request(self):
        path = '/ping-' + self.probe
        rqst = 'GET ' + path + ' HTTP/1.1'
        print(rqst)
        return rqst

    def get_min_rtt_host(self):
        min = None

        for item in self.hosts_rtt:
            if min is None or item[1] < min[1]:
                min = item
                print('min', min)
        return min[0]

    def get_rtt(self):
        for host in self.hosts:
            try:
                print('try--- ', host, self.port)
                self.socket.connect((host, self.port))

                self.socket.sendall(self.generate_request().encode())
                while True:
                    rtt = self.socket.recv(1024).decode()

                    print('raw result ', rtt)
                    pattern = re.compile('round-trip min/avg/max/stddev = (.*) ms\n')
                    result = pattern.findall(rtt)[0].split('/')[1] #if len(pattern.findall(rtt)) > 0 else 0
                    print('rtt result ', result)

                    self.hosts_rtt.append((host, float(result)))
                    break
                self.socket.close()
            except:
                traceback.print_exc()
                continue

    def get_best(self):
        self.get_rtt()
        print(self.hosts_rtt)
        return self.get_min_rtt_host()
