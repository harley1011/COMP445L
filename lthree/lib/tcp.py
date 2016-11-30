import ipaddress
import socket
import threading
import queue
import math
import time
import datetime

from lib.connection_status import ConnectionStatus
from lib.packet_type import PacketType

from lib.packet import Packet


class Tcp:
    def __init__(self, router_addr, router_port, conn=None):
        self.router_addr = router_addr
        self.router_port = router_port
        self.connection_requests = queue.Queue()

        # Kinda weird but basically a tcp that is listening
        # for connections will store the connections it opens while those created by it will store the
        # listener connection that created it
        self.tcp_child_connections = {}
        self.tcp_parent_connection = None

        self.tcp_child_connections_lock = threading.Lock()
        self.send_window_lock = threading.Lock()
        self.message_queue_lock = threading.Lock()
        self.connection_requests_lock = threading.Lock()

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
        self.connection_timeout_count = 5

        self.payload_size = 1013
        self.max_seq_num = math.pow(2, 32)
        self.window_size = 10
        self.receive_window = [None] * self.window_size
        self.max_time = 5
        self.verbose = True

    def start_listening(self, port):
        self.port = port
        threading.Thread(target=self.listen_for_connections, daemon=True).start()

    def log(self, message):
        if self.verbose:
            print(message)

    def log_packet(self, header):
        if self.verbose:
            print('{}: TCP {} with peer port {}: {}'.format(datetime.datetime.now().strftime("%H:%M:%S.%f"), self.port, self.peer_port, header))

    def start_protocol(self, start_timer=True):
        threading.Thread(target=self.message_write_worker, daemon=True).start()
        threading.Thread(target=self.message_read_worker, daemon=True).start()
        if start_timer:
            threading.Thread(target=self.timer_worker, daemon=True).start()

    def recv_from(self, number_of_bytes):
        message = bytearray()

        # block while we don't have any message
        while len(self.messages_received) == 0:
            pass

        self.send_window_lock.acquire(True)

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
        self.log_packet("Passing message up: {}".format(message.decode('utf-8')))
        return bytes(message)

    def listen_for_connections(self):
        if self.connection_status == ConnectionStatus.Closed:
            self.connection_status = ConnectionStatus.Listening
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.connection.settimeout(10)
            self.connection.bind(('', self.port))
            self.start_protocol()

    def send(self, peer_addr, peer_port, message):
        self.log_packet("Sending message {}".format(message))
        if self.connection_status == ConnectionStatus.Closed:
            self.peer_addr = peer_addr
            self.peer_port = peer_port
            self.send_syn()
            self.connection_status = ConnectionStatus.Handshake
            self.start_protocol()
        self.message_queue_lock.acquire(True)
        self.messages_to_send.append(message)
        self.message_queue_lock.release()

    def message_write_worker(self):
        while self.connection_status == ConnectionStatus.Listening or self.connection_status == ConnectionStatus.Handshake:
            pass

        while self.connection_status == ConnectionStatus.Open:
            self.message_queue_lock.acquire(True)
            if len(self.messages_to_send) > 0:
                current_message = self.messages_to_send.pop(0)
                self.message_queue_lock.release()
                while len(current_message) > 0:
                    self.send_window_lock.acquire(True)
                    while len(self.send_window) < self.window_size and len(current_message) > 0:
                        to_send = current_message[:self.payload_size]
                        current_message = current_message[self.payload_size:]
                        p = Packet(packet_type=PacketType.DATA.value,
                                   seq_num=self.send_seq_num,
                                   peer_ip_addr=self.peer_ip,
                                   peer_port=self.peer_port,
                                   payload=to_send)
                        # store the packet in-case we have to send it again
                        try:
                            self.log_packet("Sending packet type {} with message {}".format(PacketType(p.packet_type).name , p.payload.decode('utf-8')))
                        except:
                            self.log_packet("Sending packet type {}".format(PacketType(p.packet_type).name))

                        self.send_seq_num = (self.send_seq_num + 1) % (self.max_seq_num + 1)
                        packet_and_timer = {'packet': p, 'timer': time.time()}
                        self.send_window.append(packet_and_timer)
                        self.log_packet("Send Window Size {}".format(len(self.send_window)))
                        try:
                            self.send_packet(p)
                        except:
                            if self.connection_status == ConnectionStatus.Terminated:
                                self.log_packet('Message write worker terminating')
                                self.send_window_lock.release()
                                return
                        # give a change for others to use the window so acks can be handled and
                        # we can removed things from the window
                        self.send_window_lock.release()
                        self.send_window_lock.acquire(True)
                    self.send_window_lock.release()
            else:
                self.message_queue_lock.release()

    def timer_worker(self):
        while self.connection_status != ConnectionStatus.Closed and self.connection_status != ConnectionStatus.Terminated:
            self.send_window_lock.acquire(True)
            for i in range(len(self.send_window)):
                packet_and_timer = self.send_window[i]
                if packet_and_timer is None:
                    continue

                p = packet_and_timer['packet']
                timer = packet_and_timer['timer']
                now = time.time()
                elapsed = now - timer

                if elapsed >= self.max_time:
                    try:
                        packet_and_timer['ttl'] -= 1
                    except:
                        packet_and_timer['ttl'] = 20

                    if packet_and_timer['ttl'] == 0:
                        self.log_packet('Packet {} ttl reached, removing packet from window'.format(p.seq_num))
                        self.send_window[i] = None
                    else:
                        self.log_packet('Re-sending packet {} of type {}'.format(p.seq_num, PacketType(p.packet_type).name))
                        packet_and_timer['timer'] = time.time()
                        self.send_packet(p)
            self.send_window_lock.release()
        self.log_packet('Timer worker terminating for tcp with peer port {}'.format(self.peer_port))

    def message_read_worker(self):
        while self.connection_status != ConnectionStatus.Closed:
            data = ''
            try:
                data, addr = self.connection.recvfrom(1024)
            except:
                # This allows the thread to die, or else the thread would never end because recvfrom is blocking without a timeout
                if self.connection_status == ConnectionStatus.Terminated:
                    self.log_packet('Message read worker terminating')
                    return
                else:
                    if self.connection_timeout_count == 0:
                        self.log_packet("Tcp connection hasn't heard from peer connection, terminating connection")
                        self.close()
                        return
                    else:
                        self.connection_timeout_count -= 1
                    continue
            try:
                p = Packet.from_bytes(data)
                try:
                    if len(p.payload) > 0:
                        self.log_packet("Received Packet {} type {} with msg: {}\r\n".format(p.seq_num, PacketType(p.packet_type).name, p.payload.decode('utf-8')))
                    else:
                        self.log_packet("Received Packet {} type {} received".format(p.seq_num, PacketType(p.packet_type).name))
                except:
                    self.log_packet("Received Packet {} type {} received".format(p.seq_num, PacketType(p.packet_type).name))

                if self.connection_status != ConnectionStatus.Listening and self.peer_port != p.peer_port:
                    self.peer_port = p.peer_port

                if p.packet_type == PacketType.SYN.value:
                    self.handle_syn(p, addr)
                elif p.packet_type == PacketType.SYN_ACK.value:
                    # Check if it's a duplicate message
                    self.handle_syn_ack(p)
                elif p.packet_type == PacketType.ACK.value and self.connection_status == ConnectionStatus.Open:
                     self.handle_ack(p)
                elif p.packet_type == PacketType.NAK.value and self.connection_status == ConnectionStatus.Open:
                    self.handle_nack(p)
                elif p.packet_type == PacketType.DATA.value and self.connection_status != ConnectionStatus.Listening:
                    if self.connection_status == ConnectionStatus.Handshake:
                        self.connection_status = ConnectionStatus.Open
                    self.handle_data(p)
            except Exception:
                self.log_packet("Error something went wrong in message_read_worker data is : {}".format(data))

    def handle_syn(self, p, addr):
        self.tcp_child_connections_lock.acquire(True)
        self.log_packet("Handle SYN")
        if not self.check_if_duplicate_syn(p.peer_ip_addr, p.peer_port):
            self.log_packet("Added peer port to queue")
            self.connection_requests.put({'packet': p})
            self.tcp_child_connections["{}:{}".format(p.peer_ip_addr, p.peer_port)] = "Waiting"
        else:
            self.log_packet("Peer connection already open or waiting to open ")
        self.tcp_child_connections_lock.release()

    def check_if_duplicate_syn(self, peer_ip_addr, peer_port):
        return '{}:{}'.format(peer_ip_addr, peer_port) in self.tcp_child_connections

    def accept(self):
        # lock here because it's possible we are putting something at the same time we are
        # getting
        #self.connection_requests_lock.acquire(True)
        packet_and_addr = self.connection_requests.get()
        #self.connection_requests_lock.release()
        p = packet_and_addr['packet']
        self.log_packet('Accepting TCP connection')

        # create new socket for the tcp connection
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.bind(('', 0))
        conn.settimeout(10)

        tcp = Tcp(self.router_addr, self.router_port, conn)
        #store the tcp connection
        self.tcp_child_connections_lock.acquire(True)
        self.tcp_child_connections['{}:{}'.format(p.peer_ip_addr, p.peer_port)] = tcp
        self.tcp_child_connections_lock.release()
        tcp.port = conn.getsockname()[1]
        tcp.connection_status = ConnectionStatus.Handshake
        tcp.peer_ip = p.peer_ip_addr
        tcp.peer_port = p.peer_port
        tcp.rec_seq_num = (p.seq_num+1) % (tcp.max_seq_num + 1)
        tcp.start_protocol()
        tcp.tcp_parent_connection = self

        #self.send_syn_ack(p, tcp.connection.getsockname()[1])

        tcp.send_syn_ack(p, tcp.connection.getsockname()[1])

        while tcp.connection_status != ConnectionStatus.Open:
            pass

        tcp.handle_ack(p)

        return tcp, p.peer_port

    def handle_syn_ack(self, p):
        self.log_packet('Handle SYN ACK')
        if self.connection_status is ConnectionStatus.Open:
            return
        self.rec_seq_num = (self.rec_seq_num + 1) % (self.max_seq_num + 1)
        self.peer_port = int(p.payload.decode("utf-8"))
        self.connection_status = ConnectionStatus.Open
        self.handle_ack(p)

    def handle_ack(self, p):
        self.log_packet('Handle ACK for packet {}'.format(p.seq_num))
        self.send_window_lock.acquire(True)

        for i in range(len(self.send_window)):
            packet_and_timer = self.send_window[i]
            if packet_and_timer is None:
                continue
            if p.seq_num == packet_and_timer['packet'].seq_num:
                self.send_window[i] = None
                self.log_packet('Packet {} removed from send window'.format(p.seq_num))
                break
            elif i == len(self.send_window)-1:
                self.send_window_lock.release()
                return

        self.evaluate_send_window()
        self.send_window_lock.release()

    def handle_nack(self, p):
        self.log_packet('Handle NAK')

    def handle_data(self, p):
        self.log_packet('Handling data for packet {}'.format(p.seq_num))
        index = p.seq_num - self.rec_seq_num if self.rec_seq_num <= p.seq_num else \
            (1 + self.max_seq_num - self.rec_seq_num) + p.seq_num
        index = int(index)

        if index < self.window_size:
            self.receive_window[index] = p
            self.log_packet("Storing payload in window at index {} payload is {}".format(index, p.payload))
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

            d = self.receive_window.pop(0).payload
            self.log_packet("Adding to message queue {}".format(d))
            self.messages_received.append(d)
            self.receive_window.append(None)
            self.rec_seq_num = (self.rec_seq_num + 1) % (self.max_seq_num + 1)

    def send_syn_ack(self, p, port):
        p.payload = str(port).encode("utf-8")
        p.packet_type = PacketType.SYN_ACK.value

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
        self.log_packet("Sending SYN")

    def send_ack(self, num):
        self.log_packet("Sending ACK for seq {}".format(num))
        p = Packet(packet_type=PacketType.ACK.value,
                   seq_num=num,
                   peer_ip_addr=self.peer_ip,
                   peer_port=self.peer_port,
                   payload='')
        self.send_packet(p)

    def send_packet(self, p):
        try:
            b = p.to_bytes()
            self.connection.sendto(b, (self.router_addr, self.router_port))
            self.port = self.connection.getsockname()[1]
        except:
            self.log_packet("Error can't send packet {}".format(p.seq_num))

    def remove_tcp_child_connection(self, peer_ip_addr, peer_poor):
        self.tcp_child_connections_lock.acquire(True)
        self.log_packet("Child connection with peer port {} being remove from connection pool".format(peer_poor))
        self.tcp_child_connections.pop('{}:{}'.format(peer_ip_addr, peer_poor))
        self.tcp_child_connections_lock.release()

    def close(self):
        # since we don't have a terminate handshake wait for any possible duplicate packets
        # in-case our ACKs were dropped or delayed too long
        #time.sleep(1)
        self.connection_status = ConnectionStatus.Terminated
        self.connection.settimeout(0)
        self.connection.close()
        if self.tcp_parent_connection is not None:
            self.tcp_parent_connection.remove_tcp_child_connection(self.peer_ip, self.peer_port)