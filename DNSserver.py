# https://www.cnblogs.com/dongkuo/p/6714071.html
# http://c.biancheng.net/view/6457.html
import socket
import DNSPacket
import traceback
import time
import sys
import MeasureClient
import urllib
import json
import threading
import Queue
from math import sin, cos, sqrt, atan2, radians

TTL = 240

EC2_HOST = {
    'ec2-34-238-192-84.compute-1.amazonaws.com': '34.238.192.84',  # N. Virginia
    'ec2-13-231-206-182.ap-northeast-1.compute.amazonaws.com': '13.231.206.182',  # Tokyo
    'ec2-13-239-22-118.ap-southeast-2.compute.amazonaws.com': '13.239.22.118',  # Sydney
    'ec2-34-248-209-79.eu-west-1.compute.amazonaws.com': '34.248.209.79',  # Ireland
    'ec2-18-231-122-62.sa-east-1.compute.amazonaws.com': '18.231.122.62',  # Sao Paulo
    'ec2-3-101-37-125.us-west-1.compute.amazonaws.com': '3.101.37.125'  # N. California
}


def get_location(ip):
    """
    Use api to get the location of ip
    :param ip
    :return
    the Latitude and Longitude
    """
    response = urllib.urlopen('http://ip-api.com/json/' + ip)
    resp_json = json.load(response)
    print(resp_json['lat'], resp_json['lon'])
    return resp_json['lat'], resp_json['lon']


def cal_dis(client, host):
    """
    Calculate the distance between client and host
    :param client: the Latitude and Longitude of client
    :param host: the Latitude and Longitude of host
    :return
    The distance between client and host
    """
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(client[0])
    lon1 = radians(client[1])
    lat2 = radians(host[0])
    lon2 = radians(host[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # in km

    return distance


def get_dis_to_client(client_ip):
    """
    Get the Queue of  distance between each EC2 host and client
    :param client_ip: ip of client
    :return
    The Queue of  distance distance between each EC2 host and client
    """

    # get the client location
    client = get_location(client_ip)
    host_dis = Queue.Queue()

    threads = []

    # use for loop to get each ec2 host's ip then cal the distance and put it into queue
    for host in EC2_HOST.keys():
        host_ip = EC2_HOST[host]
        t = threading.Thread(target=lambda q, arg1: q.put((host, cal_dis(client, get_location(arg1)))),
                             args=(host_dis, host_ip))
        t.start()
        threads.append(t)
    while threads:
        threads.pop().join()
    print('+++++++++++++++++++++++++++++++++++++++++')
    print(host_dis)
    print('+++++++++++++++++++++++++++++++++++++++++')

    return host_dis


def get_nearest_3(host_dis):
    """
    Get the Queue of  distance between each EC2 host and client
    :param host_dis: the queue of host distance
    :return
    The 3 nearest distance between replica server and client
    """
    dis_tuple_ls = sorted(list(host_dis.queue), key=lambda x: x[1])
    # dis_tuple_ls = sorted(host_dis.items(), key=lambda x: x[1])
    sorted_hosts = map(lambda x: x[0], dis_tuple_ls)
    print('sorted host ============= ', sorted_hosts)
    return sorted_hosts[:3]


class DNSserver:
    """
    This is DNS server which is listening the request and then  redirection to send clients to
    the replica server with the fastest response time.

    """

    def __init__(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp
        self.server.bind(('', port))
        self.port = port
        self.cache = {}  # client ip => (which replica to map, last time to fetch ip)
        self.measure_client = MeasureClient.MeasureClient(EC2_HOST.keys(), self.port)

    def serve_forever(self):
        try:
            while True:
                # dns request
                data, addr = self.server.recvfrom(1024)
                print('new dns <- ', addr[0])
                start = time.time()

                self.measure_client.set_probe(addr[0])

                start1 = time.time()

                # Set the 3 nearest distance between replica server and client
                self.measure_client.set_hosts(get_nearest_3(get_dis_to_client(addr[0])))
                print('++++++++++++++++++++++++++++++++++++++++++', time.time() - start1)

                dns = DNSPacket.DNSFrame(data)
                name = dns.getname()
                toip = None
                ifrom = ''

                if dns.query.type != 1 or name != DOMAIN:
                    print('diff in domain...', name, DOMAIN)
                    continue

                # cache hit
                if self.cache.__contains__(addr[0]) \
                        and time.time() - self.cache.get(addr[0])[1] <= TTL:
                    toip = self.cache.get(addr[0])[0]
                    ifrom = 'cache'
                    # update ttl
                    ttl = TTL - (time.time() - self.cache.get(addr[0])[1])
                    print('%s: %s-->%s (%s)' % (addr[0], name, toip, ifrom))
                    dns.setanswer(toip, ttl)
                    self.server.sendto(dns.pack(), addr)

                else:
                    print(self.cache)
                    if self.cache.__contains__(addr[0]):
                        print(time.time() - self.cache.get(addr[0])[1])
                    # If this is query a A record, then response it

                    # name = dns.getname()
                    # toip = None
                    ifrom = "rtt"
                    best_host = self.measure_client.get_best()
                    print(best_host)

                    # if the 3 nearest replica server all connection refused, the toip will be None
                    # then the server will listen for next client request and try to connect again
                    if best_host:
                        toip = EC2_HOST[best_host]
                    else:
                        print("All Connection refused")

                    if toip:
                        dns.setanswer(toip)
                        self.cache[addr[0]] = (toip, time.time())
                    print('%s: %s-->%s (%s)\t\t%s' % (addr[0], name, toip, ifrom, str(time.time() - start)))
                    self.server.sendto(dns.pack(), addr)
        except KeyboardInterrupt:
            self.server.close()
            print('shutdonwn...')
            return


if __name__ == "__main__":
    DOMAIN = sys.argv[2]
    PORT = int(sys.argv[1])
    sev = DNSserver(port=PORT)
    # sev.addname('*', '0.0.0.0') # default address
    print('listening...')
    sev.serve_forever()  # start DNS server

# run the server: python DNSserver.py 50004 cs5700cdn.example.com
# test: dig +short +time=2 +tries=1 -p 50004 @cs5700cdnproject.ccs.neu.edu cs5700cdn.example.com
