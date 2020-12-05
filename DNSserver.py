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
import math
import threading
import Queue

# import dnslib
TTL = 60

EC2_HOST = {
    'ec2-34-238-192-84.compute-1.amazonaws.com': '34.238.192.84',  # N. Virginia
    'ec2-13-231-206-182.ap-northeast-1.compute.amazonaws.com': '13.231.206.182',  # Tokyo
    'ec2-13-239-22-118.ap-southeast-2.compute.amazonaws.com': '13.239.22.118',  # Sydney
    'ec2-34-248-209-79.eu-west-1.compute.amazonaws.com': '34.248.209.79',  # Ireland
    'ec2-18-231-122-62.sa-east-1.compute.amazonaws.com': '18.231.122.62',  # Sao Paulo
    'ec2-3-101-37-125.us-west-1.compute.amazonaws.com': '3.101.37.125'  # N. California
}


def get_location(ip):
    response = urllib.urlopen('http://ip-api.com/json/' + ip)
    resp_json = json.load(response)
    print(resp_json['lat'], resp_json['lon'])
    return resp_json['lat'], resp_json['lon']


def cal_dis(client, host):
    return math.sqrt((host[0] - client[0]) ** 2 + (host[1] - client[1]) ** 2)


def get_dis_to_client(client_ip):
    client = get_location(client_ip)
    host_dis = Queue.Queue()

    threads = []

    for host in EC2_HOST.keys():
        host_ip = EC2_HOST[host]
        t = threading.Thread(target=lambda q, arg1: q.put((host, cal_dis(client, get_location(arg1)))),
                             args=(host_dis, host_ip))
        t.start()
        threads.append(t)
    print('======', len(threads))
    while threads:
        threads.pop().join()
    print('+++++++++++++++++++++++++++++++++++++++++')
    print(host_dis)
    print('+++++++++++++++++++++++++++++++++++++++++')

    # for host in EC2_HOST.keys():
    #     host_ip = EC2_HOST[host]
    #     location = get_location(host_ip)
    #     dis = math.sqrt((location[0] - client[0]) ** 2 + (location[1] - client[1]) ** 2)
    #
    #     host_dis[host] = dis
    #     print(host_dis)
    return host_dis


def get_nearest_3(host_dis):
    dis_tuple_ls = sorted(list(host_dis.queue), key=lambda x: x[1])
    #dis_tuple_ls = sorted(host_dis.items(), key=lambda x: x[1])
    sorted_hosts = map(lambda x: x[0], dis_tuple_ls)
    print('sorted host ============= ', sorted_hosts)
    return sorted_hosts[:3]


class DNSserver:
    def __init__(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp
        self.server.bind(('', port))
        self.port = port
        self.namemap = {}
        self.cache = {}  # client ip => (which replica to map, last time to fetch ip)
        self.measure_client = MeasureClient.MeasureClient(EC2_HOST.keys(), self.port)

    def serve_forever(self):
        try:
            while True:
                # dns request
                data, addr = self.server.recvfrom(1024)
                print('new dns <- ', addr[0])

                self.measure_client.set_probe(addr[0])

                start = time.time()
                self.measure_client.set_hosts(get_nearest_3(get_dis_to_client(addr[0])))
                print('++++++++++++++++++++++++++++++++++++++++++', time.time() - start)
                # self.measure_client.set_hosts(EC2_HOST.keys())

                dns = DNSPacket.DNSFrame(data)
                name = dns.getname()
                toip = None
                ifrom = ''

                '''
                toip = self.namemap[name]
                dns.setanswer(toip)
                self.server.sendto(dns.pack(), addr)
                continue
                '''

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

                # TODO cache --- DONE
                else:
                    print(self.cache)
                    if self.cache.__contains__(addr[0]):
                        print(time.time() - self.cache.get(addr[0])[1])
                    # If this is query a A record, then response it

                    # name = dns.getname()
                    # toip = None
                    ifrom = "rtt"
                    best_host = self.measure_client.get_best()
                    toip = EC2_HOST[best_host]

                    '''
                    if self.namemap.__contains__(name):
                        # If have record, response it
                        # dns.setip(namemap[name])
                        # socket.sendto(dns.getbytes(), self.client_address)
                        toip = self.namemap[name]
                    elif self.namemap.__contains__('*'):
                        # Response default address
                        # dns.setip(namemap['*'])
                        # socket.sendto(dns.getbytes(), self.client_address)
                        toip = self.namemap['*']
                    else:
                        # ignore it
                        # socket.sendto(data, self.client_address)
                        # socket.getaddrinfo(name,0)
                        try:
                            toip = socket.getaddrinfo(name, 0)[0][4][0]
                            ifrom = "sev"
                        # namemap[name] = toip
                        # print socket.getaddrinfo(name,0)
                        except Exception as e:
                            traceback.print_exc()
                            print('get ip fail')
                    '''
                    if toip:
                        dns.setanswer(toip)
                        self.cache[addr[0]] = (toip, time.time())
                    print('%s: %s-->%s (%s)' % (addr[0], name, toip, ifrom))
                    # pprint.pprint(t1.decode_dns_message(dns.getbytes()))
                    # print(dnslib.DNSRecord.parse(dns.getbytes()))
                    self.server.sendto(dns.pack(), addr)
                # else:
                #     # If this is not query a A record, ignore it
                #     self.server.sendto(data, addr)
        except KeyboardInterrupt:
            self.server.close()
            print('shutdonwn...')
            return

    def add_name(self, name, ip):
        self.namemap[name] = ip


if __name__ == "__main__":
    DOMAIN = sys.argv[2]
    PORT = int(sys.argv[1])
    sev = DNSserver(port=PORT)
    sev.add_name('www.aa.com', '192.168.0.1')  # add a A record
    sev.add_name('www.bb.com', '192.168.0.2')  # add a A record
    # sev.addname('*', '0.0.0.0') # default address
    print('listening...')
    sev.serve_forever()  # start DNS server

# run the server: python DNSserver.py 50004 cs5700cdn.example.com
# test: dig +short +time=2 +tries=1 -p 50004 @cs5700cdnproject.ccs.neu.edu cs5700cdn.example.com
