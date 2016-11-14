import socket
import ipaddress
import threading
from packet import Packet
from packet_type import PacketType
from connection_status import ConnectionStatus

class Tcp:
    def __init__(self, router_addr, router_port):
        self.router_addr = router_addr
        self.router_port = router_port
        self.open_connections = {}
        self.connection_status = ConnectionStatus.Closed
        self.connection = ""
        self.peer_ip = ""
        self.peer_addr = ""
        self.peer_port = 0
        self.messages_to_send = []
        self.message_recieved = []
        self.send_seq_num = 0
        self.rec_seq_num = 0
        self.window_size = 5
        self.ack_packets = 5
        self.transmitted_packets = {}
        self.payload_size = 1013

    def listen_for_connections(self, port):
        while True:
            data, sender = self.listen_for_response(port)
            #todo run on separate thread
            self.send_syn_ack(sender, data)

    def send(self, peer_addr, peer_port, message):
        if self.connection_status == ConnectionStatus.Closed:
            self.peer_addr = peer_addr
            self.peer_port = peer_port
            self.send_syn()
            p = self.wait_for_response()
            if p.packet_type == PacketType.SYN_ACK:
                self.connection_status = ConnectionStatus.Open
                threading.Thread(target=self.message_worker,
                                 daemon=True).start()
                threading.Thread(target=self.message_read_worker, daemon=True).start()

        self.messages_to_send.push(message)

    def message_write_worker(self):
        while self.connection_status == ConnectionStatus.Open:
            current_message = self.messages_to_send[0]
            while len(current_message) > 0:
                while self.ack_packets > 0:
                    self.send_seq_num += 1
                    to_send = current_message[:self.payload_size]
                    current_message = current_message[self.payload_size:]
                    p = Packet(packet_type=PacketType.DATA,
                               seq_num=self.send_seq_num,
                               peer_ip_addr=self.peer_ip,
                               peer_port=self.peer_port,
                               payload=to_send)
                    # store the packet in-case we have to send it again
                    self.transmitted_packets[self.send_seq_num] = p
                    self.send_packet(p)

    def message_read_worker(self):
        while True:
            #todo determine if packet is an ACK or data packet.
            #todo reconstruct the original message in the correct order
            data = self.connection.recvfrom(1024)

    def send_syn_ack(self, data):
        p = Packet.from_bytes(data)
        p.payload = ''
        p.packet_type = PacketType.SYN_ACK
        p.seq_num = 0
        self.connection.sendto(p.to_bytes(), self.connection)

    def send_syn(self):
        self.peer_ip = ipaddress.ip_address(socket.gethostbyname(self.peer_ip))
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        p = Packet(packet_type=PacketType.SYN,
                   seq_num=0,
                   peer_ip_addr=self.peer_ip,
                   peer_port=self.peer_port,
                   payload='')
        self.send_packet(p)

    def send_ack_and_wait(self, conn, p):
        p = Packet(packet_type=PacketType.SYN,
                   seq_num=0,
                   peer_ip_addr=self.setup_packet.peer_ip_addr,
                   peer_port=self.setup_packet.server_port,
                   payload='')
        self.send_packet(conn, p)
        p = self.wait_for_response(conn)

    def send_packet(self, p):
        self.connection.sendto(p.to_bytes(), (self.router_addr, self.router_port))
        print('Send "{}" to router'.format(p.payload))

    def wait_for_response(self, conn, timeout=5):
        try:
            self.connection.settimeout(timeout)
            print('Waiting for a response')
            response, sender = conn.recvfrom(1024)
            p = Packet.from_bytes(response)
            print('Router: ', sender)
            print('Packet: ', p)
            print('Payload: ' + p.payload.decode("utf-8"))

        except socket.timeout:
            print('No response after {}s'.format(timeout))
        return p

    def listen_for_response(self, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.connection.bind(('', port))
            while True:
                data, sender = self.connection.recvfrom(1024)
                return data, sender

        finally:
            self.connection.close()
