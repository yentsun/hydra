.. Hydra documentation master file, created by
   sphinx-quickstart on Thu Nov  7 12:42:11 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


============
Проект Hydra
============

.. image:: _static/logo.png


Цель
====

Рендеринг материалов (PDF-буклеты, PNG и т. д.) для сайтов компании. Финальная
переработка генераторов в единый пакет с "ядром" и
входными материалами проектов.

Описание
========

Проект разработан на Python 2.7 и представляет из себя типичный python-пакет.
Используются модули:

* `minidom <https://wiki.python.org/moin/MiniDom>`_ - чтение XML
* `json <http://docs.python.org/2/library/json.html>`_ - чтение/запись JSON
* `xlrd <http://www.lexicon.net/sjmachin/xlrd.html>`_ - чтение Excel-таблиц
* `art3d_utils <https://bitbucket.org/art3d-dev/art3d_utils>`_ - обработка данных о квартирах
* `art3d_pdf <https://bitbucket.org/art3d-dev/art3d_scroll/>`_ (aka Scroll) - сборка PDF-буклета

Для `серверной "логистики"` используется пакет `Fabric`_

В качестве базы данных используется `SQLite <http://www.sqlite.org/>`_.

Содержание
==========

.. toctree::
   :maxdepth: 2

   basic_operations
   config

.. _Fabric: http://docs.fabfile.org