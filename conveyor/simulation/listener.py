import queue
import threading
import socketserver

from conveyor.simulation.simulation import Conveyor


class Listener:
    # TODO: handle conveyor start/stop. out_port = 7
    def __init__(self, locks_conf: [str, int, int], conveyor: Conveyor=None):
        """
        Base simulation listener class

        Must handle commands like:
            - OUTPUT <out_port(int)> <value(0|1)>
            - INPUT <in_port(int)>

        that works with GPI-mock and operates with Conveyor simulation locks
        """
        self.conveyor = conveyor
        self.command_map = {
            'OUTPUT': self.handle_output,
            'INPUT': self.handle_input
        }
        self.in_ports, self.out_ports = zip(*[(in_p, out_p) for _, in_p, out_p in locks_conf])
        self.handle_queue = queue.Queue()

    def fetch_conveyor(self, conveyor: Conveyor):
        self.conveyor = conveyor

    def handler(self, data: bytes):
        """ Main handler function, that chooses handler function for the command"""
        self.handle_queue.put(f'-> Received: {data.decode("utf8")}\n')
        try:
            data = str(data, 'utf-8')
            command, *args = data.split(' ')
            command_handler = self.command_map[command.upper()]
            result = command_handler(*args)
        except (ValueError, KeyError) as e:
            result = f'NOT OK, exception: {e}'.encode('utf8')
        self.handle_queue.put(f'<- Response: {result.decode("utf8")}\n')
        return result

    def handle_output(self, out_port, value):
        """ Open/Close lock """
        out_port, value = int(out_port), int(value)
        action_map = {1: self.conveyor.lock_open,
                      0: self.conveyor.lock_close}
        action_map[value](self.out_ports.index(out_port))
        return b'OK'

    def handle_input(self, in_port):
        """ Get status of the lock """
        in_port = int(in_port)
        lock_status = self.conveyor.way.locks[self.in_ports.index(in_port)].is_empty()
        return str(int(not lock_status)).encode('utf8')  # 'not' is for inverting

    def start(self):
        if self.conveyor is not None:
            self._start()
        else:
            raise RuntimeError('You need to fetch conveyor to listener at first')

    def _start(self):
        """ Need to be implemented in children  """
        raise NotImplemented

    def stop(self):
        raise NotImplemented


class SocketServerListener(Listener):
    def __init__(self, locks_conf: [str, int, int], conveyor: Conveyor=None, host='localhost', port=42024):
        """ Listener based on the simple socketserver in the thread """
        super().__init__(locks_conf, conveyor)
        server, handler = self.prepare_server_and_handler(self.handler)
        self.server = server((host, port), handler)

    def prepare_server_and_handler(self, handler):
        class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
            def handle(self):
                # self.rfile is a file-like object created by the handler;
                # we can now use e.g. readline() instead of raw recv() calls
                data = self.rfile.readline().strip()
                result = handler(data)
                # Likewise, self.wfile is a file-like object used to write back
                # to the client
                self.wfile.write(result)

        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            _block_on_close = True

        return ThreadedTCPServer, ThreadedTCPRequestHandler

    def _start(self):
        """ Start server in the thread """
        server_thread = threading.Thread(target=self.server.serve_forever, daemon=False)
        server_thread.start()

    def stop(self):
        self.server.server_close()
        self.server.shutdown()
