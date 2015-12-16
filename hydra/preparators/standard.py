# -*- coding: utf-8 -*-

from art3dutils.utilities import mass_replace, DICTIONARY_1S

LAND_NOTATION = {
    u'Выгрузка': 'output',
    u'd2p1:ТипНедвижимости': 'building_type',
    'xmlns:d3p1': 'title',
    u'd3p1:ОбъектСтроительства': 'phase',
    u'd4p1:ЗемельныйУчасток': 'apartment',
    'xmlns:d4p1': 'number',
    u'РеквизитыЗемельногоУчастка': 'data',
    u'ПлощадьЗУ': 'square',
    u'СтоимостьЗУ': 'total_cost',
    u'ДоступностьКпродаже': 'status',
}


def cyrillic_to_standard(data_string):
    """Translate cyrillic nodes to normal xml"""
    new_data_string = mass_replace(data_string.decode('utf-8'), DICTIONARY_1S)
    return new_data_string


def art3d_data_js(data_string):
    """Clean art3d js for json validation (multiple blocks)"""
    new_data_string = data_string.split(';')[0].replace('var data=', '')
    return new_data_string


def art3d_data_js_single(data_string):
    """Clean art3d js for json validation (single block)"""
    new_data_string = data_string.replace('var data = ', '')
    return new_data_string


def absolut_land_notation(data_string):
    """Replace Absolut's cyrillic notation"""
    for key in LAND_NOTATION:
        data_string = data_string.replace(key, LAND_NOTATION[key])

    return data_string