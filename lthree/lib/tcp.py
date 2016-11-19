import ipaddress
import socket
import threading
import math
import time

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
        self.messages_received = []
        self.send_seq_num = 0
        self.rec_seq_num = 0
        self.window_size = 5
        self.send_window = []
        self.send_window_lock = threading.Lock()
        self.receive_window = [None] * self.window_size
        self.payload_size = 1013
        self.max_seq_num = math.pow(2, 32)
        self.max_time = 1

    def start_listening(self, port):
        self.port = port
        threading.Thread(target=self.listen_for_connections, daemon=True).start()

    def listen_for_connections(self):
        if self.connection_status == ConnectionStatus.Closed:
            self.connection_status = ConnectionStatus.Listening
            data, sender = self.listen_for_response(self.port)
            self.connection_status = ConnectionStatus.Open
            p = Packet.from_bytes(data)
            if p.packet_type == PacketType.SYN.value:
                self.send_syn_ack(p)
                threading.Thread(target=self.message_write_worker, daemon=True).start()
                threading.Thread(target=self.message_read_worker, daemon=True).start()
                threading.Thread(target=self.timer_worker, daemon=True).start()

    def send(self, peer_addr, peer_port, message):
        if self.connection_status == ConnectionStatus.Closed:
            self.peer_addr = peer_addr
            self.peer_port = peer_port
            self.send_syn()
            p = self.wait_for_response()
            if p.packet_type == PacketType.SYN_ACK.value:
                self.connection_status = ConnectionStatus.Open
                threading.Thread(target=self.message_write_worker, daemon=True).start()
                threading.Thread(target=self.message_read_worker, daemon=True).start()
                threading.Thread(target=self.timer_worker, daemon=True).start()
        self.messages_to_send.append(message)

    def message_write_worker(self):
        while self.connection_status == ConnectionStatus.Open:
            if len(self.messages_to_send) > 0:
                current_message = self.messages_to_send.pop()
                while len(current_message) > 0:
                    while len(self.send_window) < self.window_size and len(current_message) > 0:
                        to_send = current_message[:self.payload_size]
                        current_message = current_message[self.payload_size:]
                        p = Packet(packet_type=PacketType.DATA.value,
                                   seq_num=self.send_seq_num,
                                   peer_ip_addr=self.peer_ip,
                                   peer_port=self.peer_port,
                                   payload=to_send.encode("utf-8"))
                        # store the packet in-case we have to send it again
                        self.send_seq_num = (self.send_seq_num + 1) % (self.max_seq_num + 1)
                        packet_and_timer = {'packet': p, 'timer': time.time()}
                        self.send_window.append(packet_and_timer)
                        self.send_packet(p)

    def timer_worker(self):
        while self.connection_status == ConnectionStatus.Open:
            self.send_window_lock.acquire(True)
            for packet_and_timer in self.send_window:
                if packet_and_timer is None:
                    continue

                packet = packet_and_timer['packet']
                timer = packet_and_timer['timer']
                now = time.time()
                elapsed = now - timer

                if elapsed >= self.max_time:
                    packet_and_timer['timer'] = time.time()
                    self.send_packet(packet)
            self.send_window_lock.release()

    def message_read_worker(self):
        while self.connection_status == ConnectionStatus.Open:
            data = self.connection.recvfrom(1024)
            p = Packet.from_bytes(data[0])

            print(p)

            if p.packet_type == PacketType.ACK.value:
                self.send_window_lock.acquire(True)
                self.handle_ack(p)
                self.send_window_lock.release()
            elif p.packet_type == PacketType.NAK.value:
                self.handle_nack(p)
            elif p.packet_type == PacketType.DATA.value:
                self.handle_data(p)

    def handle_ack(self, p):
        print('Handle ACK')

        for i in range(len(self.send_window)):
            packet_and_timer = self.send_window[i]
            if packet_and_timer is None:
                continue

            if p.seq_num == packet_and_timer['packet'].seq_num:
                self.send_window[i] = None
                break
            elif i == len(self.send_window)-1:
                return

        self.evaluate_send_window()

    def handle_nack(self, p):
        print('Handle NAK')

    def handle_data(self, p):
        print('Handle Data')

        index = p.seq_num - self.rec_seq_num if self.rec_seq_num <= p.seq_num else \
            (1 + self.max_seq_num - self.rec_seq_num) + p.seq_num
        index = int(index)
        if index < self.window_size:
            self.receive_window[index] = p

        self.evaluate_rec_window()
        self.send_ack(p.seq_num)

    def evaluate_send_window(self):
        while len(self.send_window) > 0:
            if self.send_window[0] is not None:
                return

            self.send_window.pop(0)

    def evaluate_rec_window(self):
        while True:
            if self.receive_window[0] is None:
                return

            self.messages_received.append(self.receive_window.pop(0).payload)
            self.receive_window.append(None)
            self.rec_seq_num = (self.rec_seq_num + 1) % (self.max_seq_num + 1)

    def send_syn_ack(self, p):
        p.payload = ''
        p.packet_type = PacketType.SYN_ACK.value
        self.peer_ip = p.peer_ip_addr
        self.peer_port = p.peer_port
        self.rec_seq_num = (p.seq_num+1) % (self.max_seq_num + 1)
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

    def send_ack(self, num):
        p = Packet(packet_type=PacketType.ACK.value,
                   seq_num=num,
                   peer_ip_addr=self.peer_ip,
                   peer_port=self.peer_port,
                   payload='')
        self.send_packet(p)

    def send_packet(self, p):
        b = p.to_bytes()
        self.connection.sendto(b, (self.router_addr, self.router_port))
        # print('Send "{}" to router'.format(p.payload))

    def wait_for_response(self, timeout=5):
        try:
            self.connection.settimeout(timeout)
            # print('Waiting for a response')
            response, sender = self.connection.recvfrom(1024)
            p = Packet.from_bytes(response)
            # print('Router: ', sender)
            # print('Packet: ', p)
            # print('Payload: ' + p.payload.decode("utf-8"))
            self.connection.settimeout(None)
            return p
        except socket.timeout:
            print('No response after {}s'.format(timeout))

    def listen_for_response(self, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connection.bind(('', port))
        while True:
            data, sender = self.connection.recvfrom(1024)
            return data, sender
