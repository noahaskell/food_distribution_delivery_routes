import optimize_and_make_links as oml

SHEET = oml.get_gsheet(test_sheet=True)


def make_add_dict():
    add_list = ['1530 Haight St San Francisco, CA 94117',
                '498 Sanchez St San Francisco, CA 94114',
                '4416 18th St San Francisco, CA 94114',
                '2288 Mission St San Francisco, CA 94110']
    street = ['1530 Haight St',
              '498 Sanchez St',
              '4416 18th St',
              '2288 Mission St']
    names = ['Haight St Market', 'La Marais', 'Mama Jis', 'Taqueria Cancun']
    email = ['hsm@hsm.com', 'pierre@lamarais.com', 'mama@mamajis.com',
             'taco@cancun.com']
    phone = ['123-3445', '432-2343', '555-5555', '911-1991']
    apt = ['', '', '', '']
    city_st = ['San Francisco, CA' for i in range(4)]
    zip_code = [x.split(' ')[-1] for x in add_list]
    diet = ['grocery', 'cafe', 'restaurant', 'restaurant']
    amount = ['x1', 'x2', 'x1', 'x1']
    all_vals = [['Name', 'Email address', 'Phone number',
                 'Street address', 'Apt / Unit #', 'City, State',
                 'Zip code', 'Dietary', '1 or 2']]
    for i in range(4):
        all_vals.append([names[i], email[i], phone[i], street[i],
                         apt[i], city_st[i], zip_code[i], diet[i],
                         amount[i]])
    add_dict = {'Ronald': {'index': 0,
                           'add_list': oml.make_address_list(all_vals),
                           'all_values': all_vals}}
    return add_dict


ADD_DICT = make_add_dict()


def test_get_gsheet():
    assert SHEET.title == 'test_for_reordering_address_lists', \
        "sheet title incorrect"
    assert isinstance(SHEET, oml.gspread.models.Spreadsheet), \
        "wrong gsheet type"
    values = SHEET.worksheet("Everything").get_all_values()
    assert len(values) == 320, "wrong number of values in Everything sheet"


def test_make_list_template():
    # check for list template, get rid of it if it's there
    init_names = oml.get_worksheet_names(SHEET)
    if 'List Template' in init_names:
        lt = SHEET.worksheet('List Template')
        SHEET.del_worksheet(lt)
    # test do_list_template function
    list_template = oml.make_list_template(SHEET, ADD_DICT)
    names_mk = oml.get_worksheet_names(SHEET)
    assert isinstance(list_template, oml.gspread.models.Worksheet), \
        "list_template is the wrong type"
    assert 'List Template' in names_mk, "List template not created"
    head = ['Name', 'Email address', 'Phone number',
            'Street address', 'Apt / Unit #', 'City, State',
            'Zip code', 'Dietary', '1 or 2']
    vals = list_template.get_all_values()
    check_list = [vals[0][i] == h for i, h in enumerate(head)]
    assert all(check_list), "list template headers don't match."


def test_make_address_dict():
    add_dict = oml.make_address_dict(SHEET)
    vals = add_dict['Beth M.']['all_values']
    assert vals[2][0] == 'Destiny Watson', "1st waypoint name wrong"
    assert vals[4][3] == '1179 Madeleine Circle', "3rd waypoint address wrong"
    assert vals[8][7] == 'Meat', "7th dietary restriction wrong"
    add_l = add_dict['Beth M.']['add_list']
    assert add_l[1] == '6209 Stella Avenue Cincinnati, OH 45224', \
        "second address in address list wrong"
    assert add_l[-1] == '544 Burr Oak Street Cincinnati, OH 45232', \
        "last address in address list wrong"


def test_read_address_sheets():
    oml.update_sheets(SHEET, ADD_DICT)
    v_dict = oml.read_address_sheets(SHEET)
    hsm_add = '1530 Haight St San Francisco, CA 94117'
    check_list = [sd['add_list'][0] == hsm_add for sd in v_dict.values()]
    assert all(check_list), "wrong first address in at least one address list"


def test_remove_route_sheets():
    oml.remove_route_sheets(SHEET)
    names = oml.get_worksheet_names(SHEET)
    num_route_lists = 0
    for n in names:
        if '~ List' in n:
            num_route_lists += 1
    assert num_route_lists == 0, "Some route worksheets were not removed."


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
    add_dict = oml.update_sheets(SHEET, ADD_DICT)
    all_vals = ADD_DICT['Ronald']['all_values']
    sheet_u = SHEET.worksheet('Ronald ~ List')
    values = sheet_u.get_all_values()
    check_list = []
    for i, row in enumerate(values):
        for j, val in enumerate(row):
            check_list.append(val == all_vals[i][j])
    assert all(check_list), "at least one updated value incorrect"
    assert 'link' in add_dict['Ronald'].keys(), "Link not added to subdict"
    SHEET.del_worksheet(sheet_u)


def test_update_sheet():
    worksheet = SHEET.add_worksheet(
        title='test_update',
        rows=5, cols=3
    )
    all_vals = ADD_DICT['Ronald']['all_values']
    drange = "A1:C5"
    oml.update_sheet(worksheet, all_vals, drange)
    values = worksheet.get_all_values()
    check_list = []
    for i, row in enumerate(values):
        for j, val in enumerate(row):
            check_list.append(val == all_vals[i][j])
    assert all(check_list), "at least one updated value incorrect"
    SHEET.del_worksheet(worksheet)


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
