import optimize_and_make_links as oml

SHEET = oml.get_gsheet(test_sheet=True)


def make_add_dict():
    add_list = ['1530 Haight St San Francisco, CA 94117',
                '498 Sanchez St San Francisco, CA 94114',
                '4416 18th St San Francisco, CA 94114',
                '2288 Mission St San Francisco, CA 94110']
    names = ['Haight St Market', 'La Marais', 'Mama Jis', 'Taqueria Cancun']
    types = ['grocery', 'cafe', 'restaurant', 'restaurant']
    all_vals = [['Name', 'Address', 'Type']]
    for i in range(4):
        all_vals.append([names[i], add_list[i], types[i]])
    add_dict = {'Ronald': {'index': 0,
                           'add_list': add_list,
                           'all_values': all_vals}}
    return add_dict


ADD_DICT = make_add_dict()


def test_get_gsheet():
    assert SHEET.title == 'test_for_reordering_address_lists', \
        "sheet title incorrect"
    assert isinstance(SHEET, oml.gspread.models.Spreadsheet), \
        "wrong gsheet type"
    values = SHEET.worksheet("Everything").get_all_values()
    assert len(values) == 298, "wrong number of values in Everything sheet"


def test_read_address_sheets():
    v_dict = oml.read_address_sheets(SHEET)
    tikkun_add = '7941 Elizabeth Street Cincinnati, OH 45231'
    check_list = [sd['add_list'][0] == tikkun_add for sd in v_dict.values()]
    assert all(check_list), "wrong first address in at least one address list"


def test_make_address_sheets():
    oml.make_address_sheets(SHEET, test_sheet=True)
    vals = SHEET.worksheet('Beth M. ~ List').get_all_values()
    assert vals[2][0] == 'Destiny Watson', "1st waypoint name wrong"
    assert vals[4][3] == '1179 Madeleine Circle', "3rd waypoint address wrong"
    assert vals[8][7] == 'Meat', "7th dietary restriction wrong"


def test_make_address_list():
    fake_glist = [['X', 'Street address', 'City, State', 'Zip code', 'Y'],
                  ['-', '123 Fake St.', 'Los Angeles, CA', '12345', '-'],
                  ['+', '5432 Wall St.', 'New York, NY', '54321', '+'],
                  ['x', '1600 Penn Ave.', 'Washington, DC', '55555', 'y']]
    add_list = oml.make_address_list(fake_glist)
    assert all([isinstance(x, str) for x in add_list]), \
        "at least one non-string in address list"
    assert add_list[0] == "123 Fake St. Los Angeles, CA 12345", \
        "incorrect first address in fake address list"
    assert add_list[1] == "5432 Wall St. New York, NY 54321", \
        "incorrect second address in fake address list"
    assert add_list[2] == "1600 Penn Ave. Washington, DC 55555", \
        "incorrect third address in fake address list"


def test_optimize_waypoints():
    opt_dict = oml.optimize_waypoints(ADD_DICT)
    add_list = ADD_DICT['Ronald']['add_list']
    all_vals = ADD_DICT['Ronald']['all_values']
    sub_dict = opt_dict['Ronald']
    assert sub_dict['add_list'][1] == add_list[2], \
        "first waypoint should be second waypoint from original list"
    assert sub_dict['add_list'][2] == add_list[1], \
        "second waypoint should be first waypoint from original list"
    assert sub_dict['all_values'][2] == all_vals[3], \
        "all_values incorrectly reordered by optimized waypoint order"
    assert sub_dict['all_values'][3] == all_vals[2], \
        "all_values incorrectly reordered by optimized waypoint order"


def test_reorder_values():
    fake_vals = [['a', 0],
                 ['b', 1],
                 ['d', 3],
                 ['c', 2],
                 ['e', 4]]
    fake_idx = [1, 0]
    reordered = oml.reorder_values(fake_vals, fake_idx)
    temp = reordered[2]
    assert temp[0] == 'c' and temp[1] == 2, \
        "incorrect first 'waypoint'"
    temp = reordered[3]
    assert temp[0] == 'd' and temp[1] == 3, \
        "incorrect second 'waypoint'"


def test_update_sheets():
    oml.update_sheets(SHEET, ADD_DICT)
    all_vals = ADD_DICT['Ronald']['all_values']
    sheet_u = SHEET.worksheet('Ronald ~ List')
    values = sheet_u.get_all_values()
    check_list = []
    for i, row in enumerate(values):
        for j, val in enumerate(row):
            check_list.append(val == all_vals[i][j])
    assert all(check_list), "at least one updated value incorrect"
    sheet_t = SHEET.worksheet('Ronald ~ List')
    SHEET.del_worksheet(sheet_t)


def test_process_routes():
    route_dict = oml.process_routes(ADD_DICT, out_file=None)
    add_list = ADD_DICT['Ronald']['add_list']
    link = route_dict['Ronald']
    check_list = []
    for row in add_list:
        check_list.append(row.replace(' ', '+') in link)
    assert all(check_list), "at least one address missing from link"


def test_make_directions_link():
    add_list = ADD_DICT['Ronald']['add_list']
    link = oml.make_directions_link(add_list)
    check_list = []
    for row in add_list:
        check_list.append(row.replace(' ', '+') in link)
    assert all(check_list), "at least one address missing from link"
