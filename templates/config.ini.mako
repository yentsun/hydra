[input_data]
iterator = standard.ExcelIterator
source = data.xlsx
filters = data_filter

[iterator]
start_row = 1

[iterator:data_map]
building_number = A
section_number = B
floor_number = C
number = D
room_count = E
square = F
status = G

[project:data_renderer]
apartment = building_number, section_number, floor_number, number, room_count, square, status
floor = available_total
building = available_total

[apartment]
id_pattern = {building_number}-{number}
assets = booklet

[floor]
id_pattern = {building_number}-{section_number}-{number}
width = 1000
height = 1000
assets = data, image

[section]
id_pattern = {building_number}-{number}
width = 150
height = 150

[building]
id_pattern = {number}

[remote:staging]
webroot = ???.loc