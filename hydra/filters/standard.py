from art3dutils.models import ATTR_TYPES
from art3dutils.utilities import process_value


def data_filter(lot_dict):
    """Force types for attributes on apartment dict"""
    if lot_dict:
        for attr_name, value in lot_dict.items():
            if attr_name in ATTR_TYPES:
                if type(value) not in (list, dict):
                    value = process_value(value, ATTR_TYPES[attr_name][1])
                if value is not None:
                    lot_dict[attr_name] = value
    return lot_dict


def number_filter(lot_dict):
    """Reads apt number from composite value"""
    separators = ['-', '.']
    number_str = lot_dict['number']
    for separator in separators:
        if separator in number_str:
            lot_dict['number'] = number_str.split(separator)[-1]
    return lot_dict


def quarter_building_number(lot_dict):
    """Splits quarter and building numbers"""
    quarter_number, building_number = lot_dict['building_number'].split('-')
    lot_dict['quarter_number'] = quarter_number
    lot_dict['building_number'] = building_number

    return lot_dict


def required_filter(lot_dict):
    """Filter out dicts without number and square"""
    required_attrs = ['number', 'square']
    for attr in required_attrs:
        if attr not in lot_dict or not lot_dict[attr]:
            return None
    return lot_dict


def price_required_filter(lot_dict):
    """Filter apartments not on sale"""
    if 'cost_per_meter' not in lot_dict or \
            not lot_dict['cost_per_meter']:
        return None
    return lot_dict


def no_first_floor(lot_dict):
    """Filter lots on first floor (usually commercial)"""
    if int(lot_dict['floor_number']) == 1:
        return None
    return lot_dict


def default_status(lot_dict):
    """Populate missing status"""
    if 'status' not in lot_dict:
        lot_dict['status'] = 0
    return lot_dict


def no_cost_no_status(lot_dict):
    """Set status to 0 if there's no cost"""
    no_cost_values = ['0', '0.0000', '', u'']
    if 'cost_per_meter' not in lot_dict or\
       'total_cost' not in lot_dict or\
       lot_dict['cost_per_meter'] in no_cost_values or\
       lot_dict['total_cost'] in no_cost_values:
        lot_dict['status'] = 0
    return lot_dict