import socket
import traceback
import re


class MeasureClient:
    def __init__(self, host_names, port):

        self.probe = ''
        self.hosts = host_names
        self.hosts_rtt = []  # (host, rtt)
        self.port = port

    def set_probe(self, client_ip):
        self.probe= client_ip

    def set_hosts(self, hosts):
        self.hosts = hosts

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
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, self.port))
                s.sendall(self.generate_request().encode())
                while True:
                    rtt = s.recv(1024).decode()

                    print('raw result ', rtt)
                    pattern = re.compile('round-trip min/avg/max/stddev = (.*) ms\n')
                    result = pattern.findall(rtt)[0].split('/')[1] #if len(pattern.findall(rtt)) > 0 else 0
                    print('rtt result ', result)

                    self.hosts_rtt.append((host, float(result)))
                    break
                s.close()
            except:
                traceback.print_exc()
                continue

    def get_best(self):
        self.get_rtt()
        print(self.hosts_rtt)
        return self.get_min_rtt_host()
