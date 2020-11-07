import optimize_and_make_links as oml


# not entirely sure how best to test this function...
# def test_reset_test_sheet():
#    reset_dict = oml.reset_test_sheet(update=False)


def test_get_gsheet():
    sheet = oml.get_gsheet(test_sheet=True)
    assert sheet.title == 'test_for_reordering_address_lists', \
        "sheet title incorrect"
    assert isinstance(sheet, oml.gspread.models.Spreadsheet), \
        "wrong gsheet type"
    values = sheet.worksheet("Everything").get_all_values()
    assert len(values) == 298, "wrong number of values in Everything sheet"


def test_read_address_sheets():
    pass
