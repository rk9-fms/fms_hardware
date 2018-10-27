import queue
import tkinter as tk

from conveyor.config import locks_rpi_config

import conveyor.simulation.config as sim_conf
from conveyor.simulation.simulation import Way, Conveyor
from conveyor.simulation.listener import SocketServerListener, Listener


def prepare_formated_ascii(way: Way):
    """ Template engine for template in the config """
    palette = '[*]'
    no_palette = '   '

    format_list = []
    for element in way:
        if element.is_empty():
            element_ascii = no_palette
        else:
            element_ascii = palette
        format_list.append(element_ascii)
    return sim_conf.template_for_format.format(*format_list)


def print_formatted_way(way: Way):
    print(prepare_formated_ascii(way))


class TkVisualiser:
    def __init__(self, conveyor: Conveyor, listener: Listener):
        """ Visualiser based on tkinter """
        self.conveyor = conveyor
        self.conveyor.stop_assembly_line()
        self._add_conveyor_open_and_close_callbacks()  # hack with open/close callbacks

        self.listener = listener
        self.listener.fetch_conveyor(conveyor)

        self.root = self.init_root()

        visualiser_frame = tk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)

        # visualisation text widget
        self.text = tk.Text(visualiser_frame,
                            bg='black', fg='white',
                            height=sim_conf.template_height, width=sim_conf.template_width)
        self.text.pack(side=tk.TOP)

        # simulation speed control frame
        self.create_sim_speed_frame(visualiser_frame).pack(side=tk.TOP, fill=tk.X)

        # assembly line control frame
        self.create_assembly_line_frame(visualiser_frame).pack(side=tk.TOP, fill=tk.X)

        # deploy pad control frame
        self.create_deploy_frame(visualiser_frame).pack(side=tk.TOP, fill=tk.X)

        # locks control frame
        locks_frame, self.locks_statuses_labels = self.create_locks_frame(visualiser_frame)
        locks_frame.pack(side=tk.TOP, fill=tk.X)

        # reset button
        reset_button = tk.Button(visualiser_frame, text='Reset visualisation')
        reset_button.pack(side=tk.BOTTOM)
        reset_button.bind("<Button-1>", lambda event: self.conveyor.reset())

        visualiser_frame.pack(side=tk.LEFT)

        # listener log frame
        listener_frame, self.listener_log_text = self.create_listener_frame(self.root)
        listener_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.root.after(50, self._listener_logger)

        self._visualisation_loop(self.conveyor.visualisation_queue)
        self.conveyor.start_assembly_line()

    def _add_conveyor_open_and_close_callbacks(self):
        """ Hack for adding callbacks to conveyor.lock_open / conveyor.lock_close methods """
        old_open_foo = self.conveyor.lock_open
        old_close_foo = self.conveyor.lock_close

        def lock_open_with_cb(lock_index):
            def callback():
                self.locks_statuses_labels[lock_index][0].config(text='Opened', bg='green')
            callback()
            old_open_foo(lock_index)

        def lock_close_with_cb(lock_index):
            def callback():
                self.locks_statuses_labels[lock_index][0].config(text='Closed', bg='red')
            callback()
            old_close_foo(lock_index)

        self.conveyor.lock_open = lock_open_with_cb
        self.conveyor.lock_close = lock_close_with_cb

    def init_root(self):
        root = tk.Tk()
        root.title('Conveyor simulation visualizer')
        root.protocol('WM_DELETE_WINDOW', self.stop)
        root.resizable(width=False, height=False)
        return root

    def create_sim_speed_frame(self, parent):
        """
        Frame for controlling simulation speed by spinbox

        | Simulation speed, s | [0.8]± |
        """

        def upd_sim_speed():
            self.conveyor.sim_speed_delay = sim_speed_var.get()

        sim_speed_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)

        sim_speed_label = tk.Label(sim_speed_frame, text='Simulation speed, s')
        sim_speed_label.pack(side=tk.LEFT, expand=1)

        sim_speed_var = tk.DoubleVar()
        sim_speed_var.set(self.conveyor.sim_speed_delay)
        sim_speed_spinbox = tk.Spinbox(sim_speed_frame,
                                       from_=0.1, to=2, increment=0.05,
                                       textvariable=sim_speed_var, command=upd_sim_speed)
        sim_speed_spinbox.pack(side=tk.LEFT, expand=1)

        return sim_speed_frame

    def create_assembly_line_frame(self, parent):
        """
        Assembly line control frame

        | Assembly line | Start | Stop |
        """
        assembly_line_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)

        assembly_line_frame_label = tk.Label(assembly_line_frame, text='Assembly line')
        assembly_line_frame_label.pack(side=tk.LEFT, expand=1)

        assembly_line_buttons_frame = tk.Frame(assembly_line_frame)

        assembly_line_start_button = tk.Button(assembly_line_buttons_frame, text='Start')
        assembly_line_start_button.pack(side=tk.LEFT)
        assembly_line_start_button.bind("<Button-1>", lambda event: self.conveyor.start_assembly_line())

        assembly_line_start_button = tk.Button(assembly_line_buttons_frame, text='Stop')
        assembly_line_start_button.pack(side=tk.LEFT)
        assembly_line_start_button.bind("<Button-1>", lambda event: self.conveyor.stop_assembly_line())

        assembly_line_buttons_frame.pack(side=tk.LEFT, expand=1)

        return assembly_line_frame

    def create_deploy_frame(self, parent):
        """
        Deploy pad control frame

        | Deploy | Deploy from Storage | Take to the Storage |
        """
        deploy_frame = tk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)

        deploy_frame_label = tk.Label(deploy_frame, text='Deploy')
        deploy_frame_label.pack(side=tk.LEFT, expand=1)

        deploy_buttons_frame = tk.Frame(deploy_frame)

        deploy_start_button = tk.Button(deploy_buttons_frame, text='Deploy from Storage')
        deploy_start_button.pack(side=tk.LEFT)
        deploy_start_button.bind("<Button-1>", lambda event: self.conveyor.place_to_conveyor())

        deploy_start_button = tk.Button(deploy_buttons_frame, text='Take to the Storage')
        deploy_start_button.pack(side=tk.LEFT)
        deploy_start_button.bind("<Button-1>", lambda event: self.conveyor.pick_from_conveyor())

        deploy_buttons_frame.pack(side=tk.LEFT, expand=1)

        return deploy_frame

    def create_locks_frame(self, parent):
        """
        Locks control frame

        |    Lock name   |
        | Opened | Empty |
        |  Open  | Close |
        |    Pass one    |
        """
        locks_frame = tk.Frame(parent)

        locks_statuses_labels = []
        for lock_index in range(4):

            # creating the frame
            lock_frame = tk.Frame(locks_frame, relief=tk.SUNKEN, borderwidth=1)

            # First row
            lock_label = tk.Label(lock_frame, text=f'Lock {lock_index + 1}')
            lock_label.pack(side=tk.TOP)

            # Second row
            lock_status_frame = tk.Frame(lock_frame)

            if self.conveyor.way.locks[lock_index].is_closed:
                text, color = 'Closed', 'red'
            else:
                text, color = 'Opened', 'green'

            lock_is_opened_label = tk.Label(lock_status_frame, text=text, width=7, bg=color)
            lock_is_opened_label.pack(side=tk.LEFT)

            lock_is_empty_status = tk.Label(lock_status_frame, text='Empty', width=7)
            lock_is_empty_status.pack(side=tk.LEFT)

            lock_status_frame.pack(side=tk.TOP)

            locks_statuses_labels.append((lock_is_opened_label, lock_is_empty_status))

            # Third row
            lock_buttons_frame = tk.Frame(lock_frame)

            lock_open_button = tk.Button(lock_buttons_frame, text='Open', width=7)
            lock_open_button.pack(side=tk.LEFT)
            lock_open_button.bind("<Button-1>", lambda event, i=lock_index: self.conveyor.lock_open(i))

            lock_open_button = tk.Button(lock_buttons_frame, text='Close', width=7)
            lock_open_button.pack(side=tk.LEFT)
            lock_open_button.bind("<Button-1>", lambda event, i=lock_index: self.conveyor.lock_close(i))

            lock_buttons_frame.pack(side=tk.TOP)

            # Fourth row
            lock_open_button = tk.Button(lock_frame, text='Pass one', width=14)
            lock_open_button.pack(side=tk.TOP)
            lock_open_button.bind("<Button-1>", lambda event, i=lock_index: self.conveyor.lock_pass_one(i))

            # Packing the frame
            lock_frame.pack(side=tk.LEFT, expand=1)

        return locks_frame, locks_statuses_labels

    def _listener_logger(self):
        """ Checks listener queue and updates text widget """
        try:
            data = self.listener.handle_queue.get(block=False)
            self.listener_log_text.insert('0.1', data)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._listener_logger)

    @staticmethod
    def create_listener_frame(parent):
        listener_frame = tk.LabelFrame(parent, relief=tk.SUNKEN, borderwidth=1, text='Listener log')

        listener_text_widget = tk.Text(listener_frame, width=30)
        listener_text_widget.pack(fill=tk.BOTH, expand=1)

        return listener_frame, listener_text_widget

    def _visualisation_loop(self, visualisation_queue: queue.Queue):
        try:
            way = visualisation_queue.get(block=False)
            self.tk_draw(way)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._visualisation_loop, visualisation_queue)

    def tk_draw(self, way: Way):
        """
        Visualisation callback

        Redraws tk.Text widget.
        Makes decisions based on assembly line elements states
        """
        self.text.delete('0.1', tk.END)
        self.text.insert('0.1', prepare_formated_ascii(way))

        for lock_i, lock in enumerate(way.locks):
            # coloring the is_open flag
            lock_status_coords = sim_conf.locks_is_open_symbols[lock_i]
            lock_is_open_tag_name = f'lock_is_open_{lock_i}'
            self.text.tag_add(lock_is_open_tag_name, *lock_status_coords[0])
            self.text.tag_add(lock_is_open_tag_name, *lock_status_coords[1])

            colour = 'red' if lock.is_closed else 'green'
            self.text.tag_config(lock_is_open_tag_name, foreground=colour)

            # coloring the not is_empty flag
            lock_status_coords = sim_conf.locks_is_empty_symbols[lock_i]
            lock_is_empty_tag_name = f'lock_is_empty_{lock_i}'
            for symb_coord in lock_status_coords:
                self.text.tag_add(lock_is_empty_tag_name, symb_coord)
            text, colour = ('Empty', 'white') if lock.is_empty() else ('Loaded', 'orange')
            self.locks_statuses_labels[lock_i][1].config(text=text, bg=colour)
            self.text.tag_config(lock_is_empty_tag_name, foreground=colour)

        # coloring deploy pad element
        deploy_pad_tag_name = 'deploy_pad_is_picking_from'
        self.text.tag_add(deploy_pad_tag_name, *sim_conf.deploy_pad_symbols[0])
        self.text.tag_add(deploy_pad_tag_name, *sim_conf.deploy_pad_symbols[1])
        colour = 'purple' if way.deploy_pad.is_picking_from else 'white'
        self.text.tag_config(deploy_pad_tag_name, foreground=colour)

    def start(self):
        self.conveyor.start_assembly_line()
        self.listener.start()
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.listener.stop()
        self.conveyor.stop_assembly_line()
        self.conveyor.quit()
        self.root.quit()


if __name__ == '__main__':
    conv = Conveyor(sim_conf.locks_coords_list, sim_conf.deploy_coord, sim_conf.conv_len)
    conv.sim_speed_delay = 0.8
    lis = SocketServerListener(locks_rpi_config)
    vis = TkVisualiser(conv, lis)
    vis.start()
