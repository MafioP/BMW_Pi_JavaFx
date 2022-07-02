import atexit
import random
import serial
import socket
import time
import platform
# PID list
pidList = [
    '0C',  # RPM
    '05',  # Coolant Temperature
    '0F',  # Intake Air Temperature
    '0B'    # Intake manifold pressure
]
HOST = "Localhost"
PORT = 4000
DELAY = 0.1
SERIALNAME = ''
MODE = 2
# Connect to serial port COM1
if platform.system().startswith('Win'):
    SERIALNAME = 'COM1'
else:
    SERIALNAME = '/dev/tty0'
if MODE != 2:
    ser = serial.Serial(SERIALNAME, 9600, bytesize=8,
                    parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE)
    print(ser)


def checksum(data):
    hexData = [chr(int(x, 16)) for x in data.split(' ')]
    sum = 0
    for i in hexData:
        sum ^= ord(i)
    sum = hex(sum)[2:]
    if sum.__len__() < 2:
        sum = '0' + sum
    return sum


# Request
def sendRequest(pid):
    request = 'B8 12 F1 04 2C 10 00 ' + pid
    xorSum = checksum(request)
    request += ' ' + xorSum.__str__()
    print("Request: " + request)
    ser.write(bytes.fromhex(request))
    time.sleep(DELAY)


# Read
def readResponse():
    readRaw = ""
    while ser.inWaiting():
        in_read = hex(int.from_bytes(ser.read(), byteorder='little'))[2:]
        if in_read.__len__() < 2:
            in_read = '0' + in_read
        readRaw += in_read
    return readRaw


def getRPM(data):
    rpm = int(data[4:], base=16) * 4
    return "rpm:" + str(rpm)


def getAirIntakeTemp(data):
    temp = int(data[4:], base=16) - 40
    return "airInTemp:" + str(temp)


def getCoolantTemp(data):
    temp = int(data[4:], base=16) - 40
    return "coolTemp:" + str(temp)


def getIntakePressure(data):
    boost = int(data[4:], base=16)*0.01
    return "boost:"+str(boost)


# Analise
def parseData(response):
    size = int(response[6:8]) * 2  # get data size *2 to get bytes
    pid = response[8 + size - 2:10 + size - 2]  # pid is located at [address](6)+[length](2)+[data](size)-2
    response = response[18:]
    print("Evaluable data: " + response)
    print("Data size = " + str(size/2))
    print("Requested PID: " + pid)
    data = response[8:8 + size]
    print("Actual data: " + data)

    value = ""
    if pid == '0c':
        value = getRPM(data)
    elif pid == '0f':
        value = getAirIntakeTemp(data)
    elif pid == '05':
        value = getCoolantTemp(data)
    elif pid == '0b':
        value = getIntakePressure(data)
    else:
        print("DATA: " + data)
    return value


def mainLoop():
    # Request main loop

    if MODE == 1:
        client_socket.connect((HOST, PORT))
        client_socket.send(b"HELLO\n")
        print("Client is ready")
        try:
            while True:
                for pid in pidList:  # For each pid in the available pid List
                    sendRequest(pid)  # Request Data
                    if ser.inWaiting():  # While time.sleep
                        readData = readResponse()  # Read incoming data
                    value = parseData(readData)
                    client_socket.send(str.encode(value + ":\n"))
        except KeyboardInterrupt:
            print("Exiting program")
    elif MODE == 2:
        client_socket.connect((HOST, PORT))
        client_socket.send(b"HELLO\n")
        print("Client is ready")
        try:
            while True:
                val1 = "rpm:" + str(random.randint(800, 4500))
                client_socket.send(str.encode(val1 + ":\n"))
                time.sleep(DELAY)
                val2 = "coolTemp:" + str(random.randint(0, 100))
                client_socket.send(str.encode(val2 + ":\n"))
                time.sleep(DELAY)
                val3 = "airInTemp:" + str(random.randint(-20, 100))
                client_socket.send(str.encode(val3 + ":\n"))
                time.sleep(DELAY)
                val4 = "boost:" + str(random.randint(0, 300)*0.01)
                client_socket.send(str.encode(val4 + ":\n"))
                time.sleep(DELAY)
        except KeyboardInterrupt:
            print("Exiting program")
    elif MODE == 3:
        try:
            while True:
                for pid in pidList:  # For each pid in the available pid List
                    sendRequest(pid)  # Request Data
                    if ser.inWaiting():  # While time.sleep
                        readData = readResponse()  # Read incoming data
                    value = parseData(readData)
                    print(value)
        except KeyboardInterrupt:
            print("Exiting Program")
    else:
        try:
            while True:
                pid = input("Input PID: ")
                sendRequest(pid)
                if ser.inWaiting():  # While time.sleep
                    readData = readResponse()  # Read incoming data
                # print(readData)
                parseData(readData)
        except KeyboardInterrupt:
            print("Exiting Program")


def exit_handler():
    print("Closing socket and serial connection")
    if MODE != 2:
        ser.close()
    client_socket.close()


if __name__ == '__main__':
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    atexit.register(exit_handler)
    mainLoop()
