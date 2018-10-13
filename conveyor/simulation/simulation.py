import time
import queue
import threading


class Rail:
    """
    Base object of the conveyor assembly line.

    Each object in the assembly line storing link to the next one
    """
    def __init__(self, next_obj=None):
        self.next_obj: Rail = next_obj
        self.palette = None

    def is_empty(self):
        return True if self.palette is None else False


class Lock(Rail):
    """ Assembly line lock """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_closed = True
        self.is_pass_one = False


class StorageDeployPad(Rail):
    """ Palettes deploy pad """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_picking_from = False


class Palette:
    """ Palette object """

    def __init__(self, way_obj: Rail):
        self.way_obj = way_obj

    def move_forward(self):
        """ The main palettes method. Here is the logic about movement decisions """
        # another palette ahead
        if not self.way_obj.next_obj.is_empty():
            return
        # in closed lock
        if isinstance(self.way_obj, Lock) and not self.way_obj.is_pass_one and self.way_obj.is_closed:
            return
        # awaiting deploy pad
        if isinstance(self.way_obj, StorageDeployPad) and self.way_obj.is_picking_from:
            self.way_obj.is_picking_from = False
            self.way_obj.palette = None
            return self
        # closed lock in pass_one mode
        if isinstance(self.way_obj, Lock) and self.way_obj.is_pass_one:
            self.way_obj.is_pass_one = False
        # replacing link to palette obj from current position to next assembly line object
        self.way_obj.palette = None
        self.way_obj.next_obj.palette = self
        # replacing link to current assembly line obj in palette
        self.way_obj = self.way_obj.next_obj


class Way:
    def __init__(self, locks_coords: [int], conv_len: int, deploy_position: int):
        """
        Assembly line container

        Represents the linked list. Contains Rails and its children, that may contains palettes

        :param [int] locks_coords: indexes of locks in list
        :param int conv_len: conveyor length
        :param int deploy_position: index of deploy pad in list
        """
        self.locks_coords = locks_coords
        self.way_len = conv_len

        self.deploy_pad: StorageDeployPad = None
        self.deploy_position = deploy_position

        self.locks: [Lock] = []
        self._way_container = []
        self.init_way()

    def init_way(self):
        """ Init the assembly line container by all coordinates """
        prev_obj: Rail = None
        first_obj = None

        for position in range(self.way_len + 1):
            if position in self.locks_coords:
                new_obj = Lock()
                self.locks.append(new_obj)
            elif position == self.deploy_position:
                new_obj = StorageDeployPad()
                self.deploy_pad = new_obj
            else:
                new_obj = Rail()

            self._way_container.append(new_obj)

            if position == 0:  # is first
                first_obj = new_obj
            if position == self.way_len:  # is last
                new_obj.next_obj = first_obj

            if prev_obj is not None:
                prev_obj.next_obj = new_obj

            prev_obj = new_obj

    def __iter__(self):
        return iter(self._way_container)


class Conveyor:
    sim_speed_delay = 0.9

    def __init__(self, locks_coords: [int], deploy_coord: int, conv_len: int):
        """
        Simulation core.

        Simulation loop runs in thread

        :param locks_coords [int]: indexes of locks in list
        :param deploy_coord: conveyor length
        :param conv_len: index of deploy pad in list
        """
        self.locks_coords = locks_coords
        self.conv_len = conv_len
        self.storage_deploy_pad_position = deploy_coord
        self.way = Way(self.locks_coords, self.conv_len, self.storage_deploy_pad_position)

        self.palettes = []

        self.visualisation_queue = queue.Queue()

        self.active = False

        self._lock = threading.Lock()
        self._conv_thread = self._start_conveyor_thread()
        self._quit = False

    def _start_conveyor_thread(self):
        thread = threading.Thread(target=self._loop_by_time, daemon=True)  # daemon for easy quit
        thread.start()
        return thread

    def lock_pass_one(self, lock_index):
        # TODO: add logic with checking not is_empty. if empty - do nothing
        # if already opened - just close
        with self._lock:
            self.way.locks[lock_index].is_pass_one = True

    def lock_open(self, lock_index):
        with self._lock:
            self.way.locks[lock_index].is_closed = False

    def lock_close(self, lock_index):
        with self._lock:
            self.way.locks[lock_index].is_closed = True

    def place_to_conveyor(self):
        self._add_palette(self.storage_deploy_pad_position)

    def pick_from_conveyor(self):
        with self._lock:
            self.way.deploy_pad: StorageDeployPad
            self.way.deploy_pad.is_picking_from = True

    def stop_assembly_line(self):
        with self._lock:
            self.active = False

    def start_assembly_line(self):
        with self._lock:
            self.active = True

    def _add_palette(self, position):
        with self._lock:
            way_obj = self.way._way_container[position]
            palette = Palette(way_obj)
            way_obj.palette = palette
            self.palettes.append(palette)

    def _loop_by_time(self):
        while True:
            if self.active:
                self._one_loop_tick()
            time.sleep(self.sim_speed_delay)
            if self._quit:
                break

    def _one_loop_tick(self):
        with self._lock:
            for palette in self.palettes[:]:
                palette_to_delete = palette.move_forward()
                if palette_to_delete:
                    self.palettes.remove(palette_to_delete)
        self.visualisation_queue.put(self.way)

    def quit(self):
        with self._lock:
            self._quit = True
        self._conv_thread.join(self.sim_speed_delay)


def print_way(way: Way):
    """ Simple visualiser for debug purpose """
    def get_ascii(element: Rail):
        ascii_element = '=' if element.is_empty() else '[*]'
        if isinstance(element, Lock):
            if element.is_pass_one:
                ascii_element = f'{{{ascii_element}>1}}'
            elif element.is_closed:
                ascii_element = f'{{{ascii_element}|}}'
            else:
                ascii_element = f'{{{ascii_element}>}}'
        if isinstance(element, StorageDeployPad):
            if element.is_picking_from:
                ascii_element = f'#{ascii_element}^#'
            else:
                ascii_element = f'#{ascii_element}>#'

        return ascii_element

    print(''.join(get_ascii(element) for element in way))


def simple_visualizer(conveyor: Conveyor):
    def vis_loop():
        while True:
            try:
                way = conveyor.visualisation_queue.get(block=False)
                print_way(way)
            except queue.Empty:
                pass
            finally:
                time.sleep(0.1)
    return threading.Thread(target=vis_loop)


if __name__ == '__main__':
    locks_coords_list = [0, 7, 15, 32]

    conv = Conveyor(locks_coords_list, 44, 54)
    simple_visualizer(conv).start()

    conv._add_palette(10)
    conv._add_palette(7)
    conv._add_palette(18)
    conv._add_palette(50)
    conv._add_palette(35)
    conv._add_palette(34)
    conv.pick_from_conveyor()
    conv.lock_open(1)

    conv.start_assembly_line()
