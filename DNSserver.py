# https://www.cnblogs.com/dongkuo/p/6714071.html
# http://c.biancheng.net/view/6457.html
import socket

class DNSserver:
    def __init__(self, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # udp
        self.server.bind(('', port))


    def serve_forever(self):

        while True:
            # dns request
            data, addr = self.server.recvfrom(1024)




    def send(self, data, addr):




        self.serer.sendto(dns_resp, addr)
