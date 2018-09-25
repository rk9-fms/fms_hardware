import socket


class ListenerProtocolClient:
    """ Base class for mocking RPI lib """
    def send_request(self, data):
        raise NotImplemented


class ListenerSocketClient(ListenerProtocolClient):
    def __init__(self, host='localhost', port=42024):
        """ Simulation listener client based on sockets """
        self.host = host
        self.port = port

    def send_request(self, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Connect to server and send data
            sock.connect((self.host, self.port))
            sock.sendall(data + b"\n")

            # Receive data from the server and shut down
            received = str(sock.recv(1024), "utf-8")
            return received


class GPIOMock:
    BOARD = 1
    OUT = 1
    IN = 1
    BCM = 1
    HIGH = 1
    LOW = 0

    def __init__(self, listener_client: ListenerProtocolClient):
        """
        RPI lib mock.

        Works based on simulation protocol client, sends requests with data like:
            - OUTPUT <out_port(int)> <value(0|1)>
            - INPUT <in_port(int)>
        """
        self.client = listener_client

    @staticmethod
    def _prepare_command(command: str, *args: list):
        args_str_list = " ".join(str(arg) for arg in args)
        return f'{command.upper()} {args_str_list}'.encode()

    @staticmethod
    def setmode(a):
        pass

    def setup(self, out_port, value):
        pass

    def output(self, out_port, value):
        command = 'OUTPUT'
        data = self._prepare_command(command, out_port, value)
        self.client.send_request(data)

    def input(self, in_port):
        command = 'INPUT'
        data = self._prepare_command(command, in_port)
        port_input = self.client.send_request(data)
        return int(port_input)

    @staticmethod
    def cleanup():
        pass

    @staticmethod
    def setwarnings(flag):
        pass
