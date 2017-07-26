#-*- coding:utf-8 -*-

import logging
from sqlalchemy import Table, Integer, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

## Настройка логгирования
handler = logging.FileHandler('db.log')
handler.setLevel(logging.DEBUG)
logger = logging.getLogger('sqlalchemy')
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

## настройка базы данных
Base = declarative_base()
engine = create_engine('sqlite:///schools.sqlite.db', echo = False)
Session = sessionmaker(bind=engine)
session = Session()

class School(Base):
    """Модель отображения:Школа
       """

    __tablename__ = 'school'
    id = Column(Integer, primary_key=True)
    code = Column(Integer)
    title = Column(String)
    ctype = Column(String)
    director = Column(String)
    place = Column(String)
    address = Column(String)
    email = Column(String)
    phone = Column(String)
    site = Column(String)

    def __repr__(self):
        return '<{}>'.format(self.title)


def db_init():
    """ Генерация базы данных
       """
    Base.metadata.create_all(engine)

def add_school(d_input):
    """
     Добавить школу
       """
    db_school = School()

    for k,v in d_input.items():
        setattr( db_school, k, v)

    session.add(db_school)

    code = True
    try:
        session.commit()
    except:
        session.rollback()
        code = False
    finally:
        session.close()

    return code
