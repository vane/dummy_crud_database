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
        # mm = mmap.mmap(self.dbfile.fileno(), 0)

    def fsize(self):
        s = os.path.getsize(self.path)
        # Logger.info(f'dbsize {s}')
        return s

    def _write_int(self, i):
        return struct.pack('<I', i)

    def _read_int(self, i):
        return struct.unpack('<I', i)[0]

    def close(self):
        self.dbfile.close()
        self.dbfile = None


class CrudIndexFile(BaseFile):

    def write(self, data):
        data, size = self._get_data(data)
        end = self.fsize()
        # calculate new number of elements
        index = self._read_size()+1
        # go to end
        self.dbfile.seek(end)
        # write data object size and data
        self._write_header(size=size, index=index, status=STATUS_OK)
        self.dbfile.write(data)
        # increase number of elements
        self._write_size(size=index)
        self.dbfile.flush()
        Logger.info('elements {} new db size {}'.format(index, end+size))

    def readall(self):
        position = INT_SIZE
        end = self.fsize()
        output = []
        while position < end:
            self.dbfile.seek(position)
            status, index, skip, size = self._read_header()
            item = self.dbfile.read(size).decode('utf-8')
            position = self.dbfile.tell()
            if status == STATUS_OK:
                output.append((item, index))
        return output

    def read(self, index):
        status, index, skip, size = self.seek_data(index, use_skip=False)
        return self.dbfile.read(size).decode('utf-8')


    def update(self, index, data):
        # seek for data
        status, idx, skip, size = self.seek_data(index)
        # get position
        position = self.dbfile.tell()
        # got ot header and override with status updated and set skip to end of file
        self.dbfile.seek(position-HEADER_SIZE)
        end = self.fsize()
        self._write_header(size=size, index=idx, status=STATUS_UPDATED, skip=end)
        # read old value
        old = self.dbfile.read(size).decode('utf-8')
        # jump to end
        self.dbfile.seek(end)
        # convert data with new size and write it
        data, size = self._get_data(data)
        self._write_header(size=size, index=idx, status=STATUS_OK, skip=0)
        self.dbfile.write(data)
        self.dbfile.flush()
        return old
    
    def delete(self, index):
        # seek for data
        status, idx, skip, size = self.seek_data(index)
        # get position
        position = self.dbfile.tell()
        # go to header and override with status deleted
        self.dbfile.seek(position-HEADER_SIZE)
        self._write_header(size=size, index=idx, status=STATUS_DELETED)
        old = self.dbfile.read(size).decode('utf-8')
        # update number of elements
        elements = self._read_size()
        self._write_size(size=elements-1)
        self.dbfile.flush()
        return old

    def size(self):
        return self._read_size()

    def seek_data(self, index, use_skip=True):
        position = INT_SIZE
        end = self.fsize()
        while position < end:
            self.dbfile.seek(position)
            status, idx, skip, size = self._read_header()
            if status == STATUS_UPDATED and use_skip:
                position = skip
            else:
                if idx == index:
                    return status, idx, skip, size
                position = self.dbfile.tell()+size
        raise IndexError(f'Index out of range {index}')

    def _get_data(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        return data, len(data)

    def _read_size(self):
        self.dbfile.seek(0)
        return self._read_int(self.dbfile.read(INT_SIZE))

    def _write_size(self, size):
        self.dbfile.seek(0)
        self.dbfile.write(self._write_int(size))

    def _write_header(self, size, index, status, skip=0):
        self.dbfile.write(self._write_int(status))
        self.dbfile.write(self._write_int(index))
        self.dbfile.write(self._write_int(skip))
        self.dbfile.write(self._write_int(size))

    def _read_header(self):
        status = self._read_int(self.dbfile.read(INT_SIZE))
        index = self._read_int(self.dbfile.read(INT_SIZE))
        skip = self._read_int(self.dbfile.read(INT_SIZE))
        size = self._read_int(self.dbfile.read(INT_SIZE))
        return status, index, skip, size


if __name__ == '__main__':
    import process_size
    fpath = 'test.db'
    if os.path.exists(fpath):
        os.remove(fpath)
    rstring = lambda size: ''.join(random.choice(string.ascii_letters) for i in range(size))
    with CrudIndexFile(fpath, 'rb+') as crud:
        for i in range(10000):
            crud.write(rstring(1000*(i+1)))
            print('size : ', process_size.convert_size(crud.fsize(), 2))
            print('pid : ', process_size.get_size())
        Logger.info('all : ', crud.readall())
        Logger.info('read index 2 : ', crud.read(index=2))
        Logger.info('remove index 3 : ', crud.delete(index=3))
        Logger.info('update index 2 : ', crud.update(index=2, data=rstring(85)))
        Logger.info('read index 9 : ', crud.read(index=9))
        Logger.info('read index 2 : ', crud.read(index=9))
        Logger.info('size : ', crud.size())
