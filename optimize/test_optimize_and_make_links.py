import optimize_and_make_links as oml


# not entirely sure how best to test this function...
# def test_reset_test_sheet():
#    reset_dict = oml.reset_test_sheet(update=False)

sheet = oml.get_gsheet(test_sheet=True)


def test_get_gsheet():
    assert sheet.title == 'test_for_reordering_address_lists', \
        "sheet title incorrect"
    assert isinstance(sheet, oml.gspread.models.Spreadsheet), \
        "wrong gsheet type"
    values = sheet.worksheet("Everything").get_all_values()
    assert len(values) == 298, "wrong number of values in Everything sheet"


def test_read_address_sheets():
    v_dict = oml.read_address_sheets(sheet)
    tikkun_add = '7941 Elizabeth Street Cincinnati, OH 45231'
    check_list = [sd['add_list'][0] == tikkun_add for sd in v_dict.values()]
    assert all(check_list), "wrong first address in at least one address list"


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


def test_optimize_waypoints():
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
    opt_dict = oml.optimize_waypoints(add_dict)
    sub_dict = opt_dict['Ronald']
    assert sub_dict['route'][1] == add_list[2], \
        "first waypoint should be second waypoint from original list"
    assert sub_dict['route'][2] == add_list[1], \
        "second waypoint should be first waypoint from original list"
    assert sub_dict['all_values'][2] == all_vals[3], \
        "all_values incorrectly reordered by optimized waypoint order"
    assert sub_dict['all_values'][3] == all_vals[2], \
        "all_values incorrectly reordered by optimized waypoint order"
