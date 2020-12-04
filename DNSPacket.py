import struct


# DNS Query
class DNSQuery:
    def __init__(self, data):
        i = 1
        self.name = ''
        self.data = data

        while True:
            d = data[i]
            if d == 0:
                break
            if d < 32:
                self.name = self.name + '.'
            else:
                self.name = self.name + chr(d)
            i = i + 1
        self.querybytes = data[0:i + 1]
        (self.type, self.classify) = struct.unpack('!HH', data[i + 1:i + 5])
        self.len = i + 5
        # print(data[self.len:])

    def pack(self):
        return self.querybytes + struct.pack('!HH', self.type, self.classify), self.data[self.len:]


# DNS Answer RRS
# this class is also can be use as Authority RRS or Additional RRS
class DNSAnswer:
    def __init__(self, ip):
        self.name = 49164
        self.type = 1
        self.classify = 1
        self.timetolive = 190
        self.datalength = 4
        self.ip = ip

    def pack(self):
        res = struct.pack('!HHHLH', self.name, self.type, self.classify, self.timetolive, self.datalength)
        s = self.ip.split('.')
        res = res + struct.pack('BBBB', int(s[0]), int(s[1]), int(s[2]), int(s[3]))
        return res


# DNS frame
# must initialized by a DNS query frame
class DNSFrame:
    def __init__(self, data):
        (self.id, self.flags, self.quests, self.answers, self.author, self.addition) = struct.unpack('>HHHHHH',
                                                                                                     data[0:12])
        self.query = DNSQuery(data[12:])

    def getname(self):
        return self.query.name

    def setip(self, ip):
        self.answer = DNSAnswer(ip)
        self.answers = 1
        self.flags = 33152

    def pack(self):
        res = struct.pack('!HHHHHH', self.id, self.flags, self.quests, self.answers, self.author, self.addition)
        res = res + self.query.pack()[0]
        if self.answers != 0:
            res = res + self.answer.pack()
        return res + self.query.pack()[1]
