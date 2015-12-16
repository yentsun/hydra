# -*- coding: utf-8 -*-

import locale
from sqlalchemy import (Column, Table, Integer, ForeignKey, Float,
                        MetaData, Boolean, VARCHAR, CHAR)
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm import relationship, mapper, class_mapper


session = None
metadata = MetaData()
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def populate_session(db_path=None, create_tables=False, outer_session=None):

    global session

    if db_path and not outer_session:
        engine = create_engine(db_path)
        session_class = scoped_session(sessionmaker(bind=engine))
        session = session_class()
        if create_tables:
            metadata.create_all(engine)
    else:
        session = outer_session

    return session


class Checksum(object):
    """A project data ckecksum record"""



checksum_table = Table('checksum', metadata,
                        Column('project_title', VARCHAR(255),
                               primary_key=True),
                        Column('checksum', CHAR(32), nullable=False),
                        mysql_engine='MyISAM', mysql_charset='utf8')

mapper(Checksum, checksum_table)
