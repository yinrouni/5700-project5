# https://www.cnblogs.com/dongkuo/p/6714071.html
# http://c.biancheng.net/view/6457.html
import socket
import DNSPacket
import traceback
import time
import sys
import MeasureClient

# import dnslib
TTL = 60

EC2_HOST = {
             'ec2-34-238-192-84.compute-1.amazonaws.com': '34.238.192.84',
            # 'ec2-13-231-206-182.ap-northeast-1.compute.amazonaws.com': '13.231.206.182',
            # 'ec2-13-239-22-118.ap-southeast-2.compute.amazonaws.com': '13.239.22.118',
            # 'ec2-34-248-209-79.eu-west-1.compute.amazonaws.com': '34.248.209.79',
            # 'ec2-18-231-122-62.sa-east-1.compute.amazonaws.com': '18.231.122.62',
            # 'ec2-3-101-37-125.us-west-1.compute.amazonaws.com': '3.101.37.125'
            }


class DNSserver:
    def __init__(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp
        self.server.bind(('', port))
        self.port = port
        self.namemap = {}
        self.cache = {}  # client ip => (which replica to map, last time to fetch ip)
        self.measure_client = None

    def serve_forever(self):
        try:
            while True:
                # dns request
                data, addr = self.server.recvfrom(1024)
                print('new dns <- ', addr[0])
                self.measure_client = MeasureClient.MeasureClient(addr[0], EC2_HOST.keys(), self.port)

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
                    ifrom='cache'
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
                        self.cache[addr[0]]=(toip, time.time())
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
    PORT = sys.argv[1]
    sev = DNSserver(port=PORT)
    sev.add_name('www.aa.com', '192.168.0.1')  # add a A record
    sev.add_name('www.bb.com', '192.168.0.2')  # add a A record
    # sev.addname('*', '0.0.0.0') # default address
    print('listening...')
    sev.serve_forever()  # start DNS server

# run the server: python DNSserver.py 50004 cs5700cdn.example.com
# test: dig +short +time=2 +tries=1 -p 50004 @cs5700cdnproject.ccs.neu.edu cs5700cdn.example.com