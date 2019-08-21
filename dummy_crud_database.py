#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import os.path
import pathlib
import mmap
import time
import struct
import string
import random
import time


STATUS_DELETED = 0
STATUS_OK = 1
STATUS_UPDATED = 2
# status(0,1,2), index(item index), skip(updated object position), size(size of object)
INT_SIZE = 4
HEADER_SIZE = 4 * INT_SIZE

class Logger:
    @staticmethod
    def info(*args, **kwargs):
        print(*args)

class BaseFile:
    def __init__(self, path, access):
        self.path = path
        exists = os.path.exists(path)
        Logger.info(f'file path exists : {exists}')
        if not exists:
            Logger.info('Create db {}'.format(self.path))
            pathlib.Path(self.path).touch()
        self.access = access
        self.dbfile = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.dbfile = open(self.path, self.access)
        if self.fsize() == 0:
            Logger.info('write initial data')
            self.dbfile.write(self._write_int(0))
            self.dbfile.seek(0)
            self.dbfile.flush()

    def fsize(self):
        s = os.path.getsize(self.path)
        return s

    def _write_int(self, i):
        return struct.pack('<I', i)

    def _read_int(self, i):
        return struct.unpack('<I', i)[0]

    def close(self):
        self.dbfile.close()
        self.dbfile = None

class IndexFile(BaseFile):
    def __init__(self, path, access):
        BaseFile.__init__(self, path=path, access=access)
        self.idx = {}

    def write(self, i, position):
        self.idx[i] = position
        self.dbfile.seek(self.fsize())
        self.dbfile.write(self._write_int(i))
        self.dbfile.write(self._write_int(position))
        self.dbfile.flush()

    def read_index(self):
        self.BaseFile = {}
        index = INT_SIZE
        end = self.fsize()
        while index < end:
            i = self._read_int(self.dbfile.read(INT_SIZE))
            position = self._read_int(self.dbfile.read(INT_SIZE))
            index += INT_SIZE*2
            self.idx[i] = position


class CrudIndexFile():

    def __init__(self, dbpath='test.db', indexpath='test.index'):
        self.base = BaseFile(path=dbpath, access='rb+')
        self.idxdata = IndexFile(path=indexpath, access='rb+')

    def __enter__(self):
        self.idxdata.__enter__()
        self.idxdata.read_index()
        self.base.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.idxdata.__exit__(exc_type, exc_val, exc_tb)
        return self.base.__exit__(exc_type, exc_val, exc_tb)

    def write(self, data):
        data, size = self._get_data(data)
        end = self.base.fsize()
        # calculate new number of elements
        index = self._read_size()+1
        # go to end
        self.base.dbfile.seek(end)
        # write data object size and data
        self._write_header(size=size, index=index, status=STATUS_OK)
        self.base.dbfile.write(data)
        # increase number of elements
        self._write_size(size=index)
        self.idxdata.write(i=index, position=end)
        self.base.dbfile.flush()

    def readall(self):
        position = INT_SIZE
        end = self.fsize()
        output = []
        while position < end:
            self.base.dbfile.seek(position)
            status, index, skip, size = self._read_header()
            item = self.base.dbfile.read(size).decode('utf-8')
            position = self.base.dbfile.tell()
            if status == STATUS_OK:
                output.append((item, index))
        return output

    def read(self, index):
        status, index, skip, size = self.seek_data(index)
        return self.base.dbfile.read(size).decode('utf-8')


    def update(self, index, data):
        # seek for data
        status, idx, skip, size = self.seek_data(index)
        # get position
        position = self.base.dbfile.tell()
        # got ot header and override with status updated and set skip to end of file
        self.base.dbfile.seek(position-HEADER_SIZE)
        end = self.base.fsize()
        self._write_header(size=size, index=idx, status=STATUS_UPDATED, skip=end)
        # read old value
        old = self.base.dbfile.read(size).decode('utf-8')
        # jump to end
        self.base.dbfile.seek(end)
        # convert data with new size and write it
        data, size = self._get_data(data)
        self._write_header(size=size, index=idx, status=STATUS_OK, skip=0)
        self.base.dbfile.write(data)
        self.base.dbfile.flush()
        return old

    def delete(self, index):
        # seek for data
        status, idx, skip, size = self.seek_data(index)
        # get position
        position = self.base.dbfile.tell()
        # go to header and override with status deleted
        self.base.dbfile.seek(position-HEADER_SIZE)
        self._write_header(size=size, index=idx, status=STATUS_DELETED)
        old = self.base.dbfile.read(size).decode('utf-8')
        # update number of elements
        elements = self._read_size()
        self._write_size(size=elements-1)
        self.base.dbfile.flush()
        return old

    def size(self):
        return self._read_size()

    def seek_data(self, index):
        position = self.idxdata.idx.get(index)
        end = self.base.fsize()
        while position < end:
            self.base.dbfile.seek(position)
            status, idx, skip, size = self._read_header()
            if status == STATUS_UPDATED and idx == index:
                position = skip
            else:
                if idx == index:
                    return status, idx, skip, size
                position = self.base.dbfile.tell()+size
        raise IndexError(f'Index out of range {index}')

    def _get_data(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return data, len(data)

    def _read_size(self):
        self.base.dbfile.seek(0)
        return self.base._read_int(self.base.dbfile.read(INT_SIZE))

    def _write_size(self, size):
        self.base.dbfile.seek(0)
        self.base.dbfile.write(self.base._write_int(size))

    def _write_header(self, size, index, status, skip=0):
        self.base.dbfile.write(self.base._write_int(status))
        self.base.dbfile.write(self.base._write_int(index))
        self.base.dbfile.write(self.base._write_int(skip))
        self.base.dbfile.write(self.base._write_int(size))

    def _read_header(self):
        status = self.base._read_int(self.base.dbfile.read(INT_SIZE))
        index = self.base._read_int(self.base.dbfile.read(INT_SIZE))
        skip = self.base._read_int(self.base.dbfile.read(INT_SIZE))
        size = self.base._read_int(self.base.dbfile.read(INT_SIZE))
        return status, index, skip, size


if __name__ == '__main__':
    import process_size
    dbpath = 'test.db'
    idxpath = 'test.index'
    if os.path.exists(dbpath):
        os.remove(dbpath)
    if os.path.exists(idxpath):
        os.remove(idxpath)
    rstring = lambda size: ''.join(random.choice(string.ascii_letters) for i in range(size))
    a = time.time()
    write_elements = 100000
    read_elements = 100000
    with CrudIndexFile() as crud:
        for i in range(write_elements+1):
            crud.write(rstring(random.randrange(100, 1000)))
        size = crud.size()
        print("write elements {} in {}".format(write_elements, time.time() - a))
        b = time.time()
        for i in range(0, read_elements+1):
            crud.read(random.randrange(1, size))
        print("read elements {} in {}".format(read_elements, time.time() - b))
        Logger.info('read index 2 : ', crud.read(index=2))
        Logger.info('remove index 3 : ', crud.delete(index=3))
        Logger.info('update index 2 : ', crud.update(index=2, data=rstring(85)))
        Logger.info('read index {} : '.format(size), crud.read(index=size))
        Logger.info('size : ', crud.size())
        Logger.info('database fsize : ', process_size.convert_size(crud.base.fsize(), 2))
        Logger.info('index fsize : ', process_size.convert_size(crud.idxdata.fsize(), 2))
        Logger.info('pid : ', process_size.get_size())
    Logger.info('total : {}'.format(time.time() - a))
