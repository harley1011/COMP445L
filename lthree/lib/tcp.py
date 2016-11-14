import ipaddress
import socket
import threading

from lib.connection_status import ConnectionStatus
from lib.packet_type import PacketType

from lib.packet import Packet


class Tcp:
    def __init__(self, router_addr, router_port):
        self.router_addr = router_addr
        self.router_port = router_port
        self.open_connections = {}
        self.connection_status = ConnectionStatus.Closed
        self.connection = ""
        self.peer_ip = ""
        self.peer_addr = ""
        self.port = 5555
        self.peer_port = 0
        self.messages_to_send = []
        self.message_received = []
        self.send_seq_num = 0
        self.rec_seq_num = 0
        self.window_size = 5
        self.ack_packets = 5
        self.transmitted_packets = {}
        self.payload_size = 1013

    def start_listening(self, port):
        self.port = port
        threading.Thread(target=self.listen_for_connections, daemon=True).start()

    def listen_for_connections(self):
        if self.connection_status == ConnectionStatus.Closed:
            self.connection_status = ConnectionStatus.Listening
            data, sender = self.listen_for_response(self.port)
            p = Packet.from_bytes(data)
            self.connection = sender
            if p.packet_type == PacketType.SYN.value:
                self.send_syn_ack(p)

    def send(self, peer_addr, peer_port, message):
        if self.connection_status == ConnectionStatus.Closed:
            self.peer_addr = peer_addr
            self.peer_port = peer_port
            self.send_syn()
            p = self.wait_for_response()
            if p.packet_type == PacketType.SYN_ACK.value:
                self.connection_status = ConnectionStatus.Open
                threading.Thread(target=self.message_worker, daemon=True).start()
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
                    p = Packet(packet_type=PacketType.DATA.value,
                               seq_num=self.send_seq_num,
                               peer_ip_addr=self.peer_ip,
                               peer_port=self.peer_port,
                               payload=to_send)
                    # store the packet in-case we have to send it again
                    self.transmitted_packets[self.send_seq_num] = p
                    self.send_packet(p)

    def message_read_worker(self):
        while True:
            # todo determine if packet is an ACK or data packet.
            # todo reconstruct the original message in the correct order
            data = self.connection.recvfrom(1024)

    def send_syn_ack(self, p):
        p.payload = ''
        p.packet_type = PacketType.SYN_ACK.value
        self.send_seq_num += 1
        p.seq_num = self.send_seq_num
        self.send_packet(p)

    def send_syn(self):
        self.peer_ip = ipaddress.ip_address(socket.gethostbyname(self.peer_addr))
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        p = Packet(packet_type=PacketType.SYN.value,
                   seq_num=self.send_seq_num,
                   peer_ip_addr=self.peer_ip,
                   peer_port=self.peer_port,
                   payload='')
        self.send_seq_num += 1
        self.send_packet(p)

    def send_ack(self,):
        p = Packet(packet_type=PacketType.SYN.value,
                   seq_num=self.send_seq_num,
                   peer_ip_addr=self.peer_ip_addr,
                   peer_port=self.server_port,
                   payload='')
        self.send_packet(p)

    def send_packet(self, p):
        self.connection.sendto(p.to_bytes(), (self.router_addr, self.router_port))
        print('Send "{}" to router'.format(p.payload))

    def wait_for_response(self, timeout=500):
        try:
            self.connection.settimeout(timeout)
            print('Waiting for a response')
            response, sender = self.connection.recvfrom(1024)
            p = Packet.from_bytes(response)
            print('Router: ', sender)
            print('Packet: ', p)
            print('Payload: ' + p.payload.decode("utf-8"))
            return p
        except socket.timeout:
            print('No response after {}s'.format(timeout))

    def listen_for_response(self, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.connection.bind(('', port))
            while True:
                data, sender = self.connection.recvfrom(1024)
                return data, sender

        finally:
            self.connection.close()
