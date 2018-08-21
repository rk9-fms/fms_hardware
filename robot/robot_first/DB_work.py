from  peewee import *
import time
import os.path as path


db = SqliteDatabase('prog_storage.db')


class OpList(Model):
    owner = CharField()
    seq_name = CharField()
    sequence = BlobField()

    class Meta:
        database = db


class MachineList(Model):
    number = CharField()

    class Meta:
        database = db


class DBMaster:
    def __init__(self):

        db.connect()
        db.create_tables([MachineList, OpList])

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
        obj = OpList.create(owner='1', seq_name=fname, sequence=seq)
        obj.save()

    def add_machine(self, mach_numb):
        try:
            MachineList.select().where(MachineList.number == mach_numb).get()
            return
        except Exception:
            pass
        robot_1 = MachineList.create(number=mach_numb)
        robot_1.save()

    # return list of operations to complete
    def get_operation(self, seq_name, mach_name):
        try:
            query = OpList.select().where(OpList.seq_name == seq_name, OpList.owner == mach_name)
            return bytes(query, encoding='utf-8')
        except Exception:
            print("No such operation")
            pass


if __name__ == '__main__':
    seq = "RS//DL 1,9999//15 SP 20,H//20 MS 101//30 DS 0,48,0//35 DS 0,0,-24//36 DS 0,-48,0//40 DS 48,0,0//50 DS 0,48,0//60 DS 48,0,0//70 DS 0,-48,0//80 DS 0,0,24//90 DS 0,72,0//100 DS 0,0,-24//110 DS -96,0,0//120 DS 0,24,0//130 DS 24,24,0//140 DS 72,0,0//150 DS 0,0,24//160 DS -48,0,0//170 DS 0,0,-24//180 DS 0,-48,0//190 DS 0,0,24//200 DS 48,72,0//210 DS 0,0,-24//220 DS -96,0,0//230 DS 0,48,0//240 DS 48,0,0//250 DS 0,-48,0//260 DS 0,0,24//300 MS 101//RN//"
    with open('stuff.txt', 'w')as stuff:
       for lex in seq.split('//'):
           stuff.write(lex)
           stuff.write('\n')

