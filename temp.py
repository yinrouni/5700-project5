
import socketserver
import struct
import socket
import t1
import pprint
import socket as socketlib
import traceback
import dnslib


# DNS Query
class SinDNSQuery:
    def __init__(self, data):
        i = 1
        self.name = ''
        while True:
            print(data.decode())
            print(data[:-4].decode())
            print(data[i])
            d = ord(data[i].decode())

            if d == 0:
                break;
            if d < 32:
                self.name = self.name + '.'
            else:
                self.name = self.name + chr(d)
            i = i + 1
        print(self.name)
        self.querybytes = data[0:i + 1]
        (self.type, self.classify) = struct.unpack('>HH', data[i + 1:i + 5])
        self.len = i + 5

    def getbytes(self, data):
        return data[:-4] + struct.pack('>HH', self.type, self.classify)


# DNS Answer RRS
# this class is also can be use as Authority RRS or Additional RRS
class SinDNSAnswer:
    def __init__(self, ip):
        self.name = 49164
        self.type = 1
        self.classify = 1
        self.timetolive = 190
        self.ip = ip
        self.datalength = 4

    def getbytes(self):
        res = struct.pack('!HHHLH', self.name, self.type, self.classify, self.timetolive, self.datalength)
        s = self.ip.split('.')
        res = res + struct.pack('BBBB', int(s[0]), int(s[1]), int(s[2]), int(s[3]))
        return res

        # res = struct.pack('!HHHLH4s', self.name, self.type, self.classify, self.timetolive, self.datalength, self.ip)
        # # s = self.ip.split('.')
        # # res = res + struct.pack('BBBB', int(s[0]), int(s[1]), int(s[2]), int(s[3]))
        # return res


# DNS frame
# must initialized by a DNS query frame
class SinDNSFrame:
    def __init__(self, data):
        (self.id, self.flags, self.quests, self.answers, self.author, self.addition) = struct.unpack('!HHHHHH',
                                                                                                    data[0:12])
        self.question_data = data[12:]

        self.packet = t1.decode_dns_message(data)
        # print('frame' ,data[12:].decode())
        self.query = self.packet['questions'][0]


    def getname(self):
        return self.query['domain_name']

    def setip(self, ip):
        self.answer = SinDNSAnswer(ip)
        self.answers = 1
        self.flags = 33152

    def getbytes(self):
        res = struct.pack('!HHHHHH', self.id, self.flags, self.quests, self.answers, self.author, self.addition)
        res = res + self.question_data
        if self.answers != 0:
            res = res + self.answer.getbytes()
        return res


# A UDPHandler to handle DNS query
class SinDNSUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        # pprint.pprint(t1.decode_dns_message(data))
        dns = SinDNSFrame(data)
        socket = self.request[1]
        namemap = SinDNSServer.namemap
        if (dns.query['query_type'] == 1):
            # If this is query a A record, then response it

            name = '.'.join(map(lambda x: x.decode(),dns.getname()))
            print(name)
            toip = None
            ifrom = "map"
            if namemap.__contains__(name):
                # If have record, response it
                # dns.setip(namemap[name])
                # socket.sendto(dns.getbytes(), self.client_address)
                toip = namemap[name]
            elif namemap.__contains__('*'):
                # Response default address
                # dns.setip(namemap['*'])
                # socket.sendto(dns.getbytes(), self.client_address)
                toip = namemap['*']
            else:
                # ignore it
                # socket.sendto(data, self.client_address)
                # socket.getaddrinfo(name,0)
                try:
                    toip = socketlib.getaddrinfo(name, 0)[0][4][0]
                    ifrom = "sev"
                # namemap[name] = toip
                # print socket.getaddrinfo(name,0)
                except Exception as e:
                    traceback.print_exc()
                    print('get ip fail')
            if toip:
                dns.setip(toip)
            print('%s: %s-->%s (%s)' % (self.client_address[0], name, toip, ifrom))
            print(dnslib.DNSRecord.parse(dns.getbytes()))
            # pprint.pprint(t1.decode_dns_message(dns.getbytes()))
            socket.sendto(dns.getbytes(), self.client_address)
        else:
            # If this is not query a A record, ignore it
            socket.sendto(data, self.client_address)


# DNS Server
# It only support A record query
# user it, U can create a simple DNS server
class SinDNSServer:
    def __init__(self, port=53):
        SinDNSServer.namemap = {}
        self.port = port

    def addname(self, name, ip):
        SinDNSServer.namemap[name] = ip

    def start(self):
        HOST, PORT = "0.0.0.0", self.port
        server = socketserver.UDPServer((HOST, PORT), SinDNSUDPHandler)
        server.serve_forever()


# Now, test it
if __name__ == "__main__":
    sev = SinDNSServer()
    sev.addname('www.aa.com', '192.168.0.1')  # add a A record
    sev.addname('www.bb.com', '192.168.0.2')  # add a A record
    # sev.addname('*', '0.0.0.0') # default address
    print('start...')
    sev.start()  # start DNS server


# Now, U can use "nslookup" command to test it
