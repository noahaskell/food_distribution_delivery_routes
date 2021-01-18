import configparser
import gspread
import gspread_formatting as gsf
from oauth2client.service_account import ServiceAccountCredentials
import googlemaps as gm
from datetime import datetime
from string import ascii_uppercase as alphabet
from time import sleep
import logging

# NOTES
# - add functionality to only process subset
#  - e.g., read in, optimize, make links for subset of ~ List sheets
# - make new_head global or make function for generating new_head?

logging.basicConfig(filename='info.log',
                    level=logging.INFO)

config = configparser.ConfigParser()
config.read('food_dist.cfg')


def get_worksheet_names(spread_sheet):
    """Get a list of worksheet names

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet

    Returns
    -------
    list
        list of names of worksheets
    """
    metadata = spread_sheet.fetch_sheet_metadata()
    sheets = metadata.get('sheets', '')
    sheet_names = []
    for sh in sheets:
        props = sh.get('properties')
        title = props.get('title')
        sheet_names.append(title)
    return sheet_names


def get_gsheet(secret='client_secret.json', test_sheet=True):
    """
    Gets google spreadsheet interface

    Parameters
    ----------
    secret : str
        name of file containing secret keys and whatnot
    test_sheet : bool
        if True, gets test sheet title, else real sheet title

    Returns
    -------
    gspread.models.Spreadsheet
        interface for spreadsheet
    """
    if test_sheet:
        sheet_title = config['sheet_name']['test']
    else:
        sheet_title = config['sheet_name']['real']

    scopes = ['https://spreadsheets.google.com/feeds',
              'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(secret, scopes)
    client = gspread.authorize(creds)
    return client.open(sheet_title)


def make_list_template(spread_sheet, add_dict, sleep_time=0.25):
    """
    Makes list template worksheet for duplicating

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet
        spreadsheet interface returned by get_gsheet()
    add_dict : dict (optional)
        dictionary returned by make_address_dict() or optimize_waypoints()

    Returns
    -------
    gspread.models.Worksheet
        retrieved or created list template worksheet

    """
    worksheet_names = get_worksheet_names(spread_sheet)
    if 'List Template' in worksheet_names:
        worksheet = spread_sheet.worksheet('List Template')
        spread_sheet.del_worksheet(worksheet)
    n_row_l, n_col_l = [], []
    for driver, subdict in add_dict.items():
        add_list = subdict['all_values']
        n_row_l.append(len(add_list))
        n_col_l.append(len(add_list[0]))
    n_row, n_col = max(n_row_l), max(n_col_l)
    data_range = "A1:" + alphabet[n_col-1] + "1"

    worksheet = spread_sheet.add_worksheet(
        title='List Template',
        rows=n_row,
        cols=n_col,
        index=1
    )

    new_head = [['Name', 'Email address', 'Phone number',
                 'Street address', 'Apt / Unit #', 'City, State',
                 'Zip code', 'Dietary', '1 or 2', '']]
    update_sheet(worksheet, new_head, data_range)
    format_worksheet(worksheet, n_row, n_col, sleep_time=sleep_time)

    return worksheet


def make_address_dict(spread_sheet):
    """
    Reads in main sheet (form responses), pulls relevant columns
    grouped by driver, creates driver-specific address sheets

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet
        spreadsheet interface returned by get_gsheet()
    sleep_time : float
        duration in seconds for pausing to avoid overloading
        the sheets API requests quota

    Returns
    -------
    dict
        keys = driver names; values = dict
            keys = all_values (list of lists), index (worksheet)
    """
    # needed cols
    # Name, Email address, Phone number, Street address, Apt / Unit #,
    # City, State; Zip code, Dietary, 1 or 2, notes
    #  1 or 2 -- transform from number of family members
    if spread_sheet.title == 'test_for_reordering_address_lists':
        sheet_name = "Everything"
        testing = True
    elif spread_sheet.title == '2020 Spring ~ Crock-Pot Dinner (Responses)':
        sheet_name = "Form Responses 1"
        testing = False
    else:
        raise ValueError('Wrong spread_sheet, dude.')
    all_values = spread_sheet.worksheet(sheet_name).get_all_values()
    headers = all_values[0]
    cols = ['Name', 'Email address', 'Phone number', 'Street address',
            'Apt / Unit #', 'City, State', 'Zip code', 'Dietary needs?',
            'Number of people in your household?', 'Dietary restrictions...']
    indices = [headers.index(c) for c in cols]
    driver_idx = headers.index('Driver')
    day_idx = [i for i, s in enumerate(headers) if 'Are you able' in s][0]
    new_head = ['Name', 'Email address', 'Phone number',
                'Street address', 'Apt / Unit #', 'City, State',
                'Zip code', 'Dietary', '1 or 2', '']
    origin = ['Tikkun Farm', 'tikkunfarm@gmail.com', '513-706-1519',
              '7941 Elizabeth Street', '', 'Cincinnati, OH',
              '45231', '', '', '']

    # construct address lists
    add_dict = {}
    drivers = list(set([x[driver_idx] for x in all_values]))
    if '' in drivers:
        drivers.remove('')
    all_val_head = [new_head, origin]
    for driver in drivers:
        add_dict[driver] = {
            'all_values': all_val_head.copy(),
            'driver_added': False
        }
    for row in all_values[1:]:  # skip headers
        temp_list = [row[j] for j in indices]
        if int(temp_list[-2]) > 6:
            temp_list[-2] = 'x2'
        elif int(temp_list[-2]) > 0:
            temp_list[-2] = 'x1'
        else:
            temp_list[-2] = ''
        temp_driver = row[driver_idx]
        if temp_driver != '':
            if 'Driver' in row[day_idx]:
                temp_list[-1] = row[day_idx]
                add_dict[temp_driver]['all_values'].append(temp_list)
                add_dict[temp_driver]['driver_added'] = True
            else:
                if add_dict[temp_driver]['driver_added']:
                    add_dict[temp_driver]['all_values'].insert(-1, temp_list)
                else:
                    add_dict[temp_driver]['all_values'].append(temp_list)
    for idx, driver in enumerate(sorted(drivers)):
        add_dict[driver].pop('driver_added')
        all_val_list = add_dict[driver]['all_values']
        add_dict[driver]['add_list'] = make_address_list(all_val_list)
        add_dict[driver]['index'] = idx + 1

    if testing:
        for driver in sorted(drivers)[5:]:
            add_dict.pop(driver)

    return add_dict


def remove_route_sheets(spread_sheet, sleep_time=0.25):
    """
    Removes existing `[Name] ~ List` worksheets from spread_sheet

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet
        spreadsheet interface returned by get_gsheet()
    """
    # get rid of old address list sheets
    metadata = spread_sheet.fetch_sheet_metadata()
    sheets = metadata.get('sheets', '')
    for sh in sheets:
        props = sh.get('properties')
        title = props.get('title')
        if '~' in title and 'list' in title.lower():
            worksheet = spread_sheet.worksheet(title)
            spread_sheet.del_worksheet(worksheet)
            sleep(sleep_time)


# NOTE will probably be obviated by make_address_sheet refactor
def read_address_sheets(spread_sheet, sleep_time=0.25):
    """
    Reads and parses addresses from sheets with titles like "[Name] ~ List"

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet
        spreadsheet interface returned by get_gsheet()
    sleep_time : float
        duration in seconds for pausing to avoid overloading
        the sheets API requests quotas

    Returns
    -------
    dict
        keys = driver names, values = dicts
            keys = title, index, add_list, all_values, link
                title = worksheet title
                index = worksheet index
                add_list = [origin, waypoints, destination]
                all_values = list of lists with all cell values from worksheet
                link = link to driver sheet
    """
    sheet_metadata = spread_sheet.fetch_sheet_metadata()
    sheets = sheet_metadata.get('sheets', '')
    values_dict = {}
    for sh in sheets:
        props = sh.get('properties')
        title = props.get('title')
        title_l = title.lower()
        index = props.get('index')
        if '~' in title and 'list' in title_l and 'self' not in title_l:
            name = title.split('~')[0].strip()
            values_dict[name] = {'index': index}
        sleep(sleep_time)

    for name in values_dict.keys():
        sheet_idx = values_dict[name]['index']
        worksheet = spread_sheet.get_worksheet(sheet_idx)
        values_dict[name]['link'] = make_sheet_link(spread_sheet, worksheet)
        values = worksheet.get_all_values()
        add_list = make_address_list(values)
        values_dict[name]['add_list'] = add_list
        values_dict[name]['all_values'] = values
        sleep(sleep_time)

    return values_dict


def make_address_list(gs_list):
    """
    Parses list of lists returned by google sheets api

    Parameters
    ----------
    gs_list : list
        list of lists from google sheets api

    Returns
    -------
    list
        list with addresses as strings
    """

    headers = gs_list[0]
    street_idx = headers.index('Street address')
    city_state_idx = headers.index('City, State')
    zip_idx = headers.index('Zip code')

    add_list = []

    for this_list in gs_list[1:]:
        street = this_list[street_idx]
        city_state = this_list[city_state_idx]
        zip_code = this_list[zip_idx]
        if 'Wilson' in street and zip_code == '45231':
            city_state = 'Mount Healthy, OH'
            if 'Avenue' not in street and 'Ave' not in street:
                street += ' Avenue'
        this_add = ' '.join([street, city_state, zip_code])
        add_list.append(this_add)
        if 'Driver' in this_list[-1]:
            break

    return add_list


def optimize_waypoints(add_dict, sleep_time=0.25):
    """
    Uses google maps api to optimize waypoints for routes

    Parameters
    ----------
    add_dict : dict
        dictionary with name: {title, index, add_list, all_values} items
        returned by read_address_sheets()
    sleep_time : float
        duration in seconds to pause in between maps client requests
        to avoid API quotas

    Returns
    -------
    dict
        dictionary with name: optimized route list items
    """
    gmap_client = gm.Client(key=config['gcloud']['api_key'])
    opt_dict = {}
    for name, v_dict in add_dict.items():
        add_list = v_dict['add_list']
        sheet_idx = v_dict['index']
        origin = add_list[0]
        destin = add_list[-1]
        waypts = add_list[1:-1]
        opt_list = gmap_client.directions(
            origin=origin,
            destination=destin,
            waypoints=waypts,
            mode='driving',
            optimize_waypoints=True
        )
        opt_idx = opt_list[0]['waypoint_order']
        opt_vals = reorder_values(v_dict['all_values'], opt_idx)
        opt_route = [origin]
        for i in opt_idx:
            opt_route.append(add_list[i+1])
        opt_route.append(destin)
        opt_dict[name] = {'add_list': opt_route,
                          'all_values': opt_vals,
                          'index': sheet_idx}
        sleep(sleep_time)
    return opt_dict


def reorder_values(values, idx):
    """
    Reorders worksheet values according to optimized indices

    Parameters
    ----------
    values : list of lists
        values from a gsheet worksheet
    idx : list of ints
        (possibly) reordered waypoint indices

    Returns
    -------
    list of lists
        cell values in the optimized order for updating worksheet
    """
    reord = []
    n_val = len(idx) + 2
    for i in range(n_val):
        if i <= 1:
            this_old = [x for x in values[i]]
            reord.append(this_old)
        else:
            this_old = [x for x in values[idx[i-2]+2]]
            reord.append(this_old)
    if n_val < len(values):
        for i in range(n_val, len(values)):
            this_old = [x for x in values[i]]
            reord.append(this_old)
    return reord


def update_sheets(spread_sheet, val_dict,
                  template=None, sleep_time=0.25):
    """
    Updates worksheets with reordered values
     - optimized route order for printing
     - original values for resetting test spreadsheet

    Parameters
    ----------
    spread_sheet : gspread.models.Spreadsheet
        returned by get_gsheet()
    val_dict : dict
        dictionary structured like that
        returned by optimize_waypoints()
    template : gspread.models.Worksheet
        template to be duplicated; if None creates new worksheet
    sleep_time : float
        duration in seconds for pausing to avoid overloading
        the sheets API request quotas

    Returns
    -------
    dict
        same as input dict, but with sheet_links added to subdicts
    """
    ss_title = spread_sheet.title
    if ss_title == 'test_for_reordering_address_lists':
        testing = True
    else:
        testing = False
    titles = [t.title for t in spread_sheet.worksheets()]
    for n, name_sub_dict in enumerate(sorted(val_dict.items())):
        name, sub_dict = name_sub_dict
        title_t = name + ' ~ List'
        sheet_idx = sub_dict['index']
        values = sub_dict['all_values']
        n_rows = len(values)
        n_cols = len(values[0])
        col_letter = alphabet[n_cols-1]
        data_range = "A1:" + col_letter + str(n_rows)
        if title_t in titles:
            worksheet = spread_sheet.worksheet(title_t)
        elif isinstance(template, gspread.models.Worksheet):
            worksheet = spread_sheet.duplicate_sheet(
                source_sheet_id=template.id,
                insert_sheet_index=sheet_idx,
                new_sheet_name=title_t
            )
        else:
            worksheet = spread_sheet.add_worksheet(
                title=title_t,
                rows=n_rows,
                cols=n_cols,
                index=sheet_idx
            )
        sleep(sleep_time)
        update_sheet(worksheet, values, data_range)
        sleep(sleep_time)
        sub_dict['link'] = make_sheet_link(spread_sheet, worksheet)
        format_worksheet(worksheet, n_row=n_rows, n_col=n_cols,
                         to_do={'init': False, 'driver': True})
        if testing and n >= 5:
            break
    return val_dict


def update_sheet(worksheet, values, data_range):
    """
    Updates values in a single worksheet

    Parameters
    ----------
    worksheet : gspread.models.Worksheet
    values : list of lists
        each nested list contains values for columns
    data_range : str
        string indicating cell range, e.g., "A1:J10", "A1:D1"
    """
    cell_list = worksheet.range(data_range)
    for cell in cell_list:
        row, col = cell.row-1, cell.col-1
        cell.value = values[row][col]
    worksheet.update_cells(cell_list)


def make_links_page(address_dict, out_file='links.html'):
    """
    Makes html page with links to worksheets and google maps directions

    Parameters
    ----------
    address_dict : dict
        dictionary with name : dict(index, link, add_list, values)
    out_file : str
        file name for links page
    """
    html_a = '<!doctype html><html lang="en"><body>'
    html_z = '</body></html>'
    par_a = '<p style="font-family:Roboto;font-size:13px">'
    links_list = []
    for name, sub_dict in sorted(address_dict.items()):
        dir_text = name + ' ~ Directions'
        dir_link = make_directions_link(sub_dict['add_list'])
        sheet_text = name + ' ~ List'
        sheet_link = sub_dict['link']
        these_links = par_a + '<a href="' + \
            sheet_link + '">' + sheet_text + \
            '</a> &#38; <a href="' + \
            dir_link + '">' + dir_text + '</a></p>'
        links_list.append(these_links)
    html = html_a + " ".join(links_list) + html_z

    with open(out_file, "w") as f:
        f.write(html)


def process_routes(address_dict, out_file='links.txt'):
    """
    Makes clickable google map directions links from address lists

    Parameters
    ----------
    address_dict : dict
        dictionary of name: route list items
    out_file : str
        string specifying filename for name: link dump

    Returns
    -------
    dict
        if out_file is None, dict with name: route items
    """

    all_routes = {}
    for name, this_route in address_dict.items():
        link = make_directions_link(this_route['add_list'])
        all_routes[name] = link

    if out_file is not None:
        with open(out_file, 'w') as f:
            for k, v in all_routes.items():
                f.write(k + '\n')
                f.write(v + '\n')
                f.write('\n')
    else:
        return all_routes


def make_sheet_link(spread_sheet, worksheet):
    "Makes link to specific worksheet"
    prefix = "https://docs.google.com/spreadsheets/d/"
    ss_id = spread_sheet.id
    infix = "/view#gid="
    ws_id = str(worksheet.id)
    return prefix + ss_id + infix + ws_id


def make_directions_link(L):
    "Formats address list as google maps directions link"

    url = 'https://www.google.com/maps/dir'
    for address in L:
        url += '/' + address.replace(' ', '+')

    return url


def format_worksheet(worksheet, n_row=None, n_col=None, sleep_time=0.25,
                     to_do={'init': True, 'driver': False}):
    """
    Formats individual worksheet

    Parameters
    ----------
    worksheet : gspread.models.Worksheet
        worksheet to be formatted
    n_row, n_col : int
        number of rows, cols; if None, determine from data in worksheet
    sleep_time : float
        delay to avoid google sheets API quota problems
    to_do : dict
        specifies initial and/or driver cell formatting
        keys 'init' and 'driver', values bool
    """
    font_fmt = gsf.cellFormat(
        textFormat=gsf.textFormat(fontSize=12)
    )
    if to_do['driver']:
        # assumes n_row, n_col are specified
        n_col_l = alphabet[n_col-1]
        gsf.format_cell_ranges(
            worksheet,
            [(n_col_l + str(n_row), font_fmt)]
        )
    if to_do['init']:
        head_fmt = gsf.cellFormat(
            textFormat=gsf.textFormat(bold=True)
        )
        diet_fmt = gsf.cellFormat(
            horizontalAlignment='RIGHT'
        )
        num_fmt = gsf.cellFormat(
            horizontalAlignment='LEFT'
        )
        note_fmt = gsf.cellFormat(
            wrapStrategy='WRAP',
            textFormat=gsf.textFormat(fontSize=10)
        )
        values = worksheet.get_all_values()
        sleep(sleep_time)
        headers = values[0]
        diet_idx = headers.index('Dietary')
        num_idx = headers.index('1 or 2')
        if n_row is None:
            n_row = len(values)
        if n_col is None:
            n_col = len(values[0])
        n_col_l = alphabet[n_col-1]
        diet_l = alphabet[diet_idx]
        num_l = alphabet[num_idx]
        gsf.format_cell_ranges(
            worksheet,
            [("A1:" + n_col_l + str(n_row), font_fmt)]
        )
        sleep(sleep_time)
        gsf.format_cell_ranges(
            worksheet,
            [("A1:" + n_col_l + "1", head_fmt)]
        )
        sleep(sleep_time)
        gsf.format_cell_ranges(
            worksheet,
            [(diet_l + "2:" + diet_l + str(n_row), diet_fmt)]
        )
        sleep(sleep_time)
        gsf.format_cell_ranges(
            worksheet,
            [(num_l + "2:" + num_l + str(n_row), num_fmt)]
        )
        sleep(sleep_time)
        gsf.format_cell_ranges(
            worksheet,
            [(n_col_l + "2:" + n_col_l + str(n_row-1), note_fmt)]
        )
        sleep(sleep_time)
        widths = [160, 230, 120, 180, 90, 120, 70, 60, 50, 230]
        for i in range(n_col):
            w = widths[i]
            letter = alphabet[i]
            gsf.set_column_width(worksheet, letter, w)
        sleep(sleep_time)


if __name__ == "__main__":
    # get spread_sheet interface
    testing = False
    date_str = str(datetime.today()) .split('.')[0]
    sleep_time = 1.5
    logging.info(date_str + ": sleep_time = " + str(sleep_time))
    logging.info(date_str + ": getting spreadsheet")
    spread_sheet = get_gsheet(test_sheet=testing)

    # make address sheets
    logging.info(date_str + ": making address sheets")
    add_dict = make_address_dict(spread_sheet)

    # get dict of address lists, worksheet values
    # logging.info(date_str + ": processing address sheets")
    # add_dict = read_address_sheets(spread_sheet, sleep_time=sleep_time)

    # optimize waypoint orders
    logging.info(date_str + ": optimizing routes")
    opt_dict = optimize_waypoints(add_dict)  # removed sleep_time=sleep_time

    # remove old route sheets; add sleep_time?
    logging.info(date_str + ": removing route worksheets")
    remove_route_sheets(spread_sheet, sleep_time=sleep_time)

    # create list_template
    list_template = make_list_template(spread_sheet, opt_dict)

    # make route worksheets with optimized routes
    logging.info(date_str + ": updating sheets")
    opt_dict = update_sheets(
        spread_sheet,
        opt_dict,
        list_template,
        sleep_time=sleep_time
    )

    # links filename, then make links and write to file
    logging.info(date_str + ": making links page")
    for ss in ':- ':
        date_str = date_str.replace(ss, '_')
    links_fname = 'links_' + date_str + '.html'
    make_links_page(opt_dict, links_fname)
