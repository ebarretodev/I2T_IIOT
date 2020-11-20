import socket
from time import sleep

class PLC():
    def __init__(self, typePLC, IP_address, Port):
        self.typePLC = typePLC
        self.dest = (IP_address, Port)
        self._setPLC()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    subheader = '5000'
    network_number = '00'
    destination_station = 'FF'
    destination_IO_number = '03FF'
    request_multi_drop = '00'
    reserved_data = '0000'
    command = '0401'
    subcommand = '0000'
    device_code = 'D*'
    head_device = '000000'
    number_device = '0000'
    request_data_length = '0000'
    value_device = ''

    def _setPLC(self):
        if self.typePLC == 'FX5CPU':
            self.destination_IO_number = '03FF'
        if self.typePLC == 'RCPU':
            self.destination_IO_number = '03FF'

    def connectPLC(self):
        self.client.connect(self.dest)


    def disconnectPLC(self):
        self.client.close()


    def _createMessage(self):
        str2 = self.reserved_data + self.command + self.subcommand + self.device_code + self.head_device + self.number_device + self.value_device
        self.request_data_length = format(len(str2), '04X')
        self.str1 = self.subheader + self.network_number + self.destination_station + self.destination_IO_number + self.request_multi_drop + self.request_data_length + str2
        return self.str1


    def _sendMessage(self, msg):
        res = ''
        while res == '':
            try:
                self.client.send(bytes(msg, 'utf-8'))
                res = str(self.client.recv(1024), 'utf-8')
            except:
                pass
        if res[0:4] == 'D000' and res[4:14] == self.str1[4:14]:
            if res[18:22] == '0000':
                if self.command == '0401':
                    return int(res[22:], 16)
                if self.command =='1401':
                    return int(self.value_device, 16)
            else:
                return res[18:22]
        else:
            return 'E#9999'

    def read_M(self, start_digit, device_num=1):
        self.command = '0401'
        self.device_code = 'M*'
        self.head_device = format(start_digit, '06')
        self.number_device = format(device_num, '04')
        self.value_device = ''
        msg = self._createMessage()
        res = self._sendMessage(msg)
        return res


    def read_D(self, start_digit, device_num=1):
        self.command = '0401'
        self.device_code = 'D*'
        self.head_device = format(start_digit, '06')
        self.number_device = format(device_num, '04')
        self.value_device = ''
        msg = self._createMessage()
        res = self._sendMessage(msg)
        return res

    def write_M(self, start_digit, value, device_num=1):
        self.command = '1401'
        self.device_code = 'M*'
        self.head_device = format(start_digit, '06')
        self.number_device = format(device_num, '04')
        self.value_device = format(value, '04X' )
        msg = self._createMessage()
        res = self._sendMessage(msg)
        return res


    def write_D(self, start_digit, value, device_num=1):
        self.command = '1401'
        self.device_code = 'D*'
        self.head_device = format(start_digit, '06')
        self.number_device = format(device_num, '04')
        self.value_device = format(value, '04X' )
        msg = self._createMessage()
        res = self._sendMessage(msg)
        return res


if __name__ == "__main__":
    #set the object PLC(typePLC, IP_address, Port)
    #typePLC can be set 'FX5CPU' or 'RCPU'
    #IP_address and Port is same as set on PLC
    fx5 = PLC('FX5CPU', '192.168.3.250', 3000)
    #necessary to connect
    fx5.connectPLC()
    #sample for reading and writing M's and D's devices
    d = 0
    for i in range(11):
        a = fx5.read_D(100)  # read the contents of a register
        print('Value from D100: ' + str(a))
        b = fx5.read_M(101)
        print('Value from M101: ' + str(b))
        c = fx5.write_D(100, i*10)
        print('Value D100 set to: ' + str(c))
        d = fx5.write_M(101, d)
        if d == 0:
            d=1
        elif d == 1:
            d=0
        print('Value M101 set to: ' + str(d))
        sleep(2)
    #If necessary, it's possible to disconnect
    fx5.disconnectPLC()