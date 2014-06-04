import socket
import os
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('localhost', 8101))
sock.listen(10)
count = 0

while True:
    connection, address = sock.accept()
    count += 1
    pid = os.fork()

    if pid == 0:
        inner_count = 0
        buf = "connection established! No." + str(address[1])
        connection.send(buf)
        while True:
            connection.recv(1024)
            inner_count += 1
            print "inner_count", inner_count

    else:
        print "server side No.", count

