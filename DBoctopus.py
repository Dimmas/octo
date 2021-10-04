#!/usr/bin/python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, BigInteger, String, Text, select
from sqlalchemy.orm import sessionmaker, mapper
import time


engine = create_engine('postgresql://postgres:Pwd@localhost:5432/postgres', pool_size=20)
Session = sessionmaker(bind=engine)
metadata = MetaData()

file_tab = Table(
    'files',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('abstract', Text),
    Column('dbytes', Integer),
    Column('fbytes', Integer),
    Column('filename', String),
    Column('fmtime', Integer),
    Column('mtime', Integer),
    Column('mtype', String),
    Column('origcharset', String),
    Column('pcbytes', String),
    Column('rcludi', String),
    Column('relevancyrating', String),
    Column('sig', BigInteger),
    Column('title', String),
    Column('url', String),
    Column('ip', String),
    Column('date', Float)
    )


class DBModel():
    def __init__(self, args=None):
        self.session = Session()
        if isinstance(args, int): args = {'id': args}

        if isinstance(args, dict):
            try:
                obj = self.session.query(self._sa_instance_state.class_).filter_by(**args).one_or_none()
                if obj is not None: args = obj.__dict__
            except Exception as e:
                print(e)
            self.__set_properties__(args)
            

    def __set_properties__(self, prop=None):
        if isinstance(prop, dict):
            for p in prop:
                if p in self.properties:
                    setattr(self, p, prop[p])


    def add(self, prop=None):
        if self.id: return self.id
        if prop: self.__set_properties__(prop)
        try:
            self.session.add(self)
            self.session.commit()
            return self.id
        except Exception as e:
            print(e)

    def __del__(self):
        try:
            self.session.close()
        except: pass


class File(DBModel):
    properties = file_tab.c.keys()  # list of fields from files tab
    
    def add(self, prop=None):
        self.date = time.time()
        return super().add(prop)
        
mapper(File, file_tab)  # join File object with table 'files' in DB

        
if __name__ == '__main__':
    action = int(input('Для настройки базы данных net_octopus нажмите 1 '))

    if action == 1:    
        print('*** Настройка octo DB ***')
        metadata.create_all(engine)
