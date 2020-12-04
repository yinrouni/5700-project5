# https://www.cnblogs.com/dongkuo/p/6714071.html
# http://c.biancheng.net/view/6457.html
import socket
import DNSPacket
import traceback
# import dnslib

class DNSserver:
    def __init__(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # udp
        self.server.bind(('', port))
        self.namemap = {}

    def serve_forever(self):
        while True:
            # dns request
            data, addr = self.server.recvfrom(1024)

            dns = DNSPacket.DNSFrame(data)

            if (dns.query.type == 1):
                # If this is query a A record, then response it

                name = dns.getname()
                toip = None
                ifrom = "map"
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
                if toip:
                    dns.setip(toip)
                print('%s: %s-->%s (%s)' % (addr[0], name, toip, ifrom))
                # pprint.pprint(t1.decode_dns_message(dns.getbytes()))
                # print(dnslib.DNSRecord.parse(dns.getbytes()))
                self.server.sendto(dns.getbytes(), addr)
            else:
                # If this is not query a A record, ignore it
                self.server.sendto(data, addr)


    def add_name(self, name, ip):
        self.namemap[name] = ip
if __name__ == "__main__":
    sev = DNSserver(port= 53)
    sev.add_name('www.aa.com', '192.168.0.1')  # add a A record
    sev.add_name('www.bb.com', '192.168.0.2')  # add a A record
    # sev.addname('*', '0.0.0.0') # default address
    print('listening...')
    sev.serve_forever()  # start DNS server