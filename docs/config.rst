Конфигурация проекта
====================

Конфигурационный файл записан в ini-формате и имеет путь
:file:`input/{имя_проекта}/config.ini`

.. highlight:: ini

Пример конфигурации::

    [input_data]
    iterator = standard.ExcelIterator
    source = %(here)s/input/es/data.xlsx
    filters = data_filter, set_type

    [iterator]
    start_row = 1
    sheet_number = quarter_number

    [iterator:data_map]
    building_number = B
    square_out = J
    square = F
    total_cost = G
    note = H, I, C, D, E

    [json]
    apartment = quarter_number, building_number, square, square_out, square_f1, square_f2, square_stead, square_stead_enc, square_stead_total, total_cost, type
    filters = squares

    [json:extras]
    square_f1 = sq1, float
    square_f2 = sq2, float
    square_stead = sqs, float
    square_stead_enc = sqse, float
    square_stead_total = sqst, float

    [apartment]
    id_pattern = {building_number}
    width = 500
    height = 500
    default_number = 1
    assets = image, booklet

    [remote:staging]
    webroot = esquire.loc


