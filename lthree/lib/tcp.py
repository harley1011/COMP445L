import ipaddress
import socket
import threading
import queue
import math
import time

from lib.connection_status import ConnectionStatus
from lib.packet_type import PacketType

from lib.packet import Packet


class Tcp:
    def __init__(self, router_addr, router_port, conn=None):
        self.router_addr = router_addr
        self.router_port = router_port
        self.connection_requests = queue.Queue()
        self.connection_status = ConnectionStatus.Closed
        self.connection = conn if (conn is not None) else ""
        self.peer_ip = ""
        self.peer_addr = ""
        self.port = 5555
        self.peer_port = 0
        self.messages_to_send = []
        self.messages_received = []
        self.send_seq_num = 0
        self.rec_seq_num = 0
        self.send_window = []
        self.send_window_lock = threading.Lock()
        self.payload_size = 1013
        self.max_seq_num = math.pow(2, 32)
        self.window_size = 5
        self.receive_window = [None] * self.window_size
        self.max_time = 0.5

    def start_listening(self, port):
        self.port = port
        threading.Thread(target=self.listen_for_connections, daemon=True).start()

    def start_protocol(self):
        threading.Thread(target=self.message_write_worker, daemon=True).start()
        threading.Thread(target=self.message_read_worker, daemon=True).start()
        threading.Thread(target=self.timer_worker, daemon=True).start()

    def recv_from(self, number_of_bytes):
        message = bytearray()
        self.send_window_lock.acquire(True)

        # block while we don't have any message
        while len(self.messages_received) == 0:
            pass

        while len(message) < number_of_bytes and len(self.messages_received) > 0:
            current_message = self.messages_received[0]
            bytes_left = number_of_bytes - len(message)
            if len(current_message) > bytes_left:
                message.extend(current_message[:bytes_left])
                self.messages_received[0] = current_message[bytes_left:]
            else:
                message.extend(current_message)
                self.messages_received.pop(0)
        self.send_window_lock.release()
        return bytes(message)

    def listen_for_connections(self):
        if self.connection_status == ConnectionStatus.Closed:
            self.connection_status = ConnectionStatus.Listening
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connection.bind(('', self.port))
            self.start_protocol()

    def send(self, peer_addr, peer_port, message):
        if self.connection_status == ConnectionStatus.Closed:
            self.peer_addr = peer_addr
            self.peer_port = peer_port
            self.send_syn()
            self.connection_status = ConnectionStatus.Handshake
            self.start_protocol()
        self.messages_to_send.append(message)

    def message_write_worker(self):
        while self.connection_status == ConnectionStatus.Listening or self.connection_status == ConnectionStatus.Handshake:
            pass

        while self.connection_status == ConnectionStatus.Open:
            if len(self.messages_to_send) > 0:
                current_message = self.messages_to_send.pop()
                while len(current_message) > 0:
                    self.send_window_lock.acquire(True)
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
                    self.send_window_lock.release()

    def timer_worker(self):
        while self.connection_status != ConnectionStatus.Closed:
            self.send_window_lock.acquire(True)
            for packet_and_timer in self.send_window:
                if packet_and_timer is None:
                    continue

                p = packet_and_timer['packet']
                timer = packet_and_timer['timer']
                now = time.time()
                elapsed = now - timer

                if elapsed >= self.max_time:
                    packet_and_timer['timer'] = time.time()
                    self.send_packet(p)

            self.send_window_lock.release()

    def message_read_worker(self):
        while self.connection_status != ConnectionStatus.Closed:
            data, addr = self.connection.recvfrom(1024)
            p = Packet.from_bytes(data)

            if self.connection_status != ConnectionStatus.Listening and self.peer_port != p.peer_port:
                self.peer_port = p.peer_port

            if p.packet_type == PacketType.SYN.value:
                self.handle_syn(p, addr)
            elif p.packet_type == PacketType.SYN_ACK.value:
                self.handle_syn_ack(p)
            elif p.packet_type == PacketType.ACK.value and self.connection_status == ConnectionStatus.Open:
                self.handle_ack(p)
            elif p.packet_type == PacketType.NAK.value and self.connection_status == ConnectionStatus.Open:
                self.handle_nack(p)
            elif p.packet_type == PacketType.DATA.value and self.connection_status != ConnectionStatus.Listening:
                if self.connection_status == ConnectionStatus.Handshake:
                    self.connection_status = ConnectionStatus.Open
                self.handle_data(p)

    def handle_syn(self, p, addr):
        # print('Handle SYN')
        self.connection_requests.put({'packet': p, 'address': addr})

    def accept(self):
        packet_and_addr = self.connection_requests.get()
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.bind(('', 0))
        p = packet_and_addr['packet']
        addr = packet_and_addr['address']

        tcp = Tcp(self.router_addr, self.router_port, conn)
        tcp.connection_status = ConnectionStatus.Handshake
        tcp.peer_ip = p.peer_ip_addr
        tcp.peer_port = p.peer_port
        tcp.rec_seq_num = (p.seq_num+1) % (tcp.max_seq_num + 1)
        tcp.send_seq_num = (tcp.send_seq_num + 1) % (tcp.max_seq_num + 1)
        tcp.start_protocol()


        self.send_syn_ack(p, tcp.connection.getsockname()[1])
        while tcp.connection_status != ConnectionStatus.Open:
            pass

        self.handle_ack(p)

        return tcp, addr

    def handle_syn_ack(self, p):
        # print('Handle SYN ACK')
        self.connection_status = ConnectionStatus.Open
        self.peer_port = int(p.payload.decode("utf-8"))
        self.handle_ack(p)

    def handle_ack(self, p):
        # print('Handle ACK')
        self.send_window_lock.acquire(True)

        for i in range(len(self.send_window)):
            packet_and_timer = self.send_window[i]
            if packet_and_timer is None:
                continue

            if p.seq_num == packet_and_timer['packet'].seq_num:
                self.send_window[i] = None
                break
            elif i == len(self.send_window)-1:
                self.send_window_lock.release()
                return

        self.evaluate_send_window()
        self.send_window_lock.release()

    def handle_nack(self, p):
        print('Handle NAK')

    def handle_data(self, p):
        # print('Handle Data')

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

    def send_syn_ack(self, p, port):
        p.payload = str(port).encode("utf-8")
        p.packet_type = PacketType.SYN_ACK.value
        self.peer_ip = p.peer_ip_addr
        self.peer_port = p.peer_port

        self.rec_seq_num = (p.seq_num+1) % (self.max_seq_num + 1)
        self.send_seq_num = (self.send_seq_num + 1) % (self.max_seq_num + 1)
        packet_and_timer = {'packet': p, 'timer': time.time()}
        self.send_window_lock.acquire(True)
        self.send_window.append(packet_and_timer)
        self.send_window_lock.release()

        self.send_packet(p)

    def send_syn(self):
        self.peer_ip = ipaddress.ip_address(socket.gethostbyname(self.peer_addr))
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        p = Packet(packet_type=PacketType.SYN.value,
                   seq_num=self.send_seq_num,
                   peer_ip_addr=self.peer_ip,
                   peer_port=self.peer_port,
                   payload='')
        self.send_seq_num = (self.send_seq_num + 1) % (self.max_seq_num + 1)
        packet_and_timer = {'packet': p, 'timer': time.time()}
        self.send_window.append(packet_and_timer)
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

    def close(self):
        self.connection_status = ConnectionStatus.Closed