import json
import os

from enum import Enum


class PaletteStatusType(Enum):
    Available = 'available'
    InTransit = 'in_transit'
    InOperation = 'in_operation'


class PalettesDB:
    """Palettes database class."""

    db_path = os.path.join(os.getcwd(), 'conveyor', 'PalettesDB.json')

    def __init__(self):
        self.db_init()
        self._db = self._load_palettes_on_lock_statistics()
        self.palettes_db = self._db['palettes_db']
        self.palettes_on_lock_db = self._db['palettes_on_lock_db']
        self.params = self._db['params']

    def db_init(self):
        """ Initialize new db if it is nor exist """

        if os.path.exists(self.db_path):
            return
        new_db = {
            'palettes_db': {},
            'palettes_on_lock_db': {'1': [], '2': [], '3': [], '4': []},
            'params': {'storage_awaiting_time': 20}
        }
        with open(self.db_path, 'w') as db:
            json.dump(new_db, db, sort_keys=True, indent=4)

    def close(self):
        """Closes palettes database."""

        self._dump_palettes_on_lock_statistics()

    def _load_palettes_on_lock_statistics(self):
        """
        Loads data from palettes database.
        :return: loaded data;
        """

        with open(self.db_path, 'r') as db:
            palettes_on_lock_db = json.load(db)
        return palettes_on_lock_db

    def _dump_palettes_on_lock_statistics(self):
        """Dumps data to palette database."""

        with open(self.db_path, 'w') as db:
            json.dump(self._db, db, sort_keys=True, indent=4)

    def pick_palette_from_storage(self):
        """
        Adds new palette to palettes database.
        :return: new palette id;
        """

        palettes_ids = self.palettes_db.keys()
        if palettes_ids:
            palette_id = int(max(palettes_ids)) + 1
        else:
            palette_id = 1
        self.palettes_db[str(palette_id)] = {'lock': 1, 'available': True, 'in_transit': False, 'in_operation': False}
        self.palettes_on_lock_db['1'].append(palette_id)
        self._dump_palettes_on_lock_statistics()
        return palette_id

    def load_palette_to_storage(self, palette_id):
        """
        Removes palette with a given id from palettes database.
        :param palette_id: palette, which should be removed;
        """

        palette_info = self.palettes_db[str(palette_id)]
        lock = palette_info['lock']
        self.palettes_db.pop(str(palette_id))
        self.palettes_on_lock_db['{}'.format(lock)].remove(palette_id)
        self._dump_palettes_on_lock_statistics()

    def get_palette_lock(self, palette_id):
        """
        Gets lock, on which palette with a given id stays.
        :param palette_id: palette, for which lock should be got;
        :return: lock, on which palette stays;
        """

        return self.palettes_db[str(palette_id)]['lock']

    def get_palette_status(self, palette_id, status_type):
        """
        Gets status with a given status type for palette with a given id.
        :param palette_id: palette, for which status should be got;
        :param status_type: type of status, which should be got for palette;
        :return: palette status;
        """

        return self.palettes_db[str(palette_id)][status_type]

    def get_palettes_on_lock(self, lock_id):
        """
        Gets list of palette ids which stays on lock with a given id.
        :param lock_id: lock, for which palettes should be got;
        :return: list contains palette ids, which stays on lock;
        """

        return list(self.palettes_on_lock_db['{}'.format(lock_id)])

    def update_palette_status(self, palette_id, status_type, status: bool):
        """
        Updates status of a given type for palette with a given id to a given value.
        :param palette_id: palette, for which status should be updated;
        :param status_type: type of status, which should be updated;
        :param status: value for status to be updated;
        """

        palette_info = self.palettes_db[str(palette_id)]
        palette_info[status_type] = status
        self._dump_palettes_on_lock_statistics()

    def remove_palette_from_lock(self, palette_id):
        """
        Removes palette with a given id from lock on which it stays.
        :param palette_id: palette, which should be removed;
        """

        old_lock_id = self.get_palette_lock(palette_id)
        self.palettes_db[str(palette_id)]['lock'] = None
        self.palettes_on_lock_db['{}'.format(old_lock_id)].remove(palette_id)
        self._dump_palettes_on_lock_statistics()

    def add_palette_to_lock(self, palette_id, lock_id):
        """
        Adds palette with a given id to lock with a given id.
        :param palette_id: palette, which should be added;
        :param lock_id: lock, on which palette should be added;
        """

        self.palettes_db[str(palette_id)]['lock'] = lock_id
        self.palettes_on_lock_db['{}'.format(lock_id)].append(palette_id)
        self._dump_palettes_on_lock_statistics()

    def get_storage_awaiting_time(self):
        """
        Gets storage awaiting time.
        :return: storage awaiting time (sec);
        """

        return self.params['storage_awaiting_time']
