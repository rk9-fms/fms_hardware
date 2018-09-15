import os.path as path
from peewee import *


def DBMaster(db_name):
    db = SqliteDatabase(db_name)

    class OpList(Model):
        seq_name = CharField()
        sequence = BlobField()

        class Meta:
            database = db

    class DBEdit:
        def __init__(self):
            db.connect()
            db.create_tables([OpList])

        # start to fill table with operation lists
        def add_list(self, filename):
            fname = path.basename(filename[:-4])
            try:
                OpList.select().where(OpList.seq_name == fname).get()
                return
            except Exception:
                pass

            with open(filename, 'r') as some_list:
                seq = some_list.read()
            obj = OpList.create(seq_name=fname, sequence=seq)
            obj.save()

        # return list of operations to complete
        def get_operation(self, seq_name):
            try:
                query = OpList.select().where(OpList.seq_name == seq_name)
                for i in query:
                    return i.sequence
            except Exception:
                print("No such operation")
                pass
    return DBEdit()
