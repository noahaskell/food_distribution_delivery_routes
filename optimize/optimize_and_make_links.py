import configparser
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import googlemaps as gm
from datetime import datetime
from string import ascii_uppercase as alphabet
from copy import deepcopy
from time import sleep

config = configparser.ConfigParser()
config.read('food_dist.cfg')


def get_gsheet(secret='client_secret.json', test_sheet=False):
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


def read_address_sheets(spread_sheet):
    """
    Reads and parses addresses from sheets with titles like "[Name] ~ List"

    Parameters
    ----------
    spread_sheet : gspread.models.SpreadSheet
        spreadsheet interface returned by get_gsheet()

    Returns
    -------
    dict
        keys = driver names, values = dicts
            keys = (worksheet) title, (worksheet) index, add_list, all_values
                add_list = [origin, waypoints, destination]
                all_values = list of lists with all cell values from worksheet
    """
    sheet_metadata = spread_sheet.fetch_sheet_metadata()
    sheets = sheet_metadata.get('sheets', '')
    values_dict = {}
    for sh in sheets:
        props = sh.get('properties')
        title = props.get('title')
        index = props.get('index')
        if '~ List' in title and 'Self' not in title:
            name = title.split('~')[0].strip()
            values_dict[name] = {'index': index}

    for name in values_dict.keys():
        sheet_idx = values_dict[name]['index']
        worksheet = spread_sheet.get_worksheet(sheet_idx)
        values = worksheet.get_all_values()
        add_list = make_address_list(values)
        values_dict[name]['add_list'] = add_list
        values_dict[name]['all_values'] = values

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


def optimize_waypoints(add_dict):
    """
    Uses google maps api to optimize waypoints for routes

    Parameters
    ----------
    add_dict : dict
        dictionary with name: {title, index, add_list, all_values} items
        returned by read_address_sheets()

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
        opt_list = gmap_client.directions(origin=origin,
                                          destination=destin,
                                          waypoints=waypts,
                                          mode='driving',
                                          optimize_waypoints=True)
        opt_idx = opt_list[0]['waypoint_order']
        opt_vals = reorder_values(v_dict['all_values'], opt_idx)
        opt_route = [origin]
        for i in opt_idx:
            opt_route.append(add_list[i+1])
        opt_route.append(destin)
        opt_dict[name] = {'route': opt_route,
                          'all_values': opt_vals,
                          'index': sheet_idx}
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


def update_sheets(spread_sheet, val_dict, sleep_time=0.1):
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
    """
    titles = [t.title for t in spread_sheet.worksheets()]
    for name, sub_dict in val_dict.items():
        title_t = name + ' ~ List'
        sheet_idx = sub_dict['index']
        values = sub_dict['all_values']
        n_rows = len(values)
        n_cols = len(values[0])
        col_letter = alphabet[n_cols-1]
        data_range = "A1:" + col_letter + str(n_rows)
        if title_t in titles:
            worksheet = spread_sheet.worksheet(title_t)
        else:
            worksheet = spread_sheet.add_worksheet(title_t,
                                                   rows=n_rows,
                                                   cols=n_cols,
                                                   index=sheet_idx)
        cell_list = worksheet.range(data_range)
        for cell in cell_list:
            row, col = cell.row-1, cell.col-1
            cell.value = values[row][col]
        worksheet.update_cells(cell_list)
        sleep(sleep_time)


def reset_test_sheet(update=True):
    """
    Resets worksheets in test spreadsheet
    """
    sheet = get_gsheet(test_sheet=True)
    work = sheet.worksheet('Everything')
    values = work.get_all_values()
    header = values[0]
    origin = ['Tikkun Farm',
              'tikkunfarm@gmail.com',
              '513-706-1519',
              '7941 Elizabeth Street',
              '',
              'Cincinnati, OH',
              '45231',
              '',
              '',
              '']
    idx = 1
    reset_dict = {}
    temp_vals = [header, origin]
    for row in values[1:]:
        temp_vals.append(row)
        if 'Driver' in row[-1]:
            name_list = row[0].split(' ')
            if len(name_list) > 1:
                name = name_list[0] + ' ' + name_list[1][0] + '.'
            else:
                name = name_list[0]
            reset_dict[name] = {'index': idx,
                                'all_values': deepcopy(temp_vals)}
            temp_vals = [header, origin]
            idx += 1
    if update:
        update_sheets(sheet, reset_dict, sleep_time=0.1)
    else:
        return reset_dict


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
        link = make_directions_link(this_route['route'])
        all_routes[name] = link

    if out_file is not None:
        with open(out_file, 'w') as f:
            for k, v in all_routes.items():
                f.write(k + '\n')
                f.write(v + '\n')
                f.write('\n')
    else:
        return all_routes


def make_directions_link(L):
    "Formats address list as google maps directions link"

    url = 'https://www.google.com/maps/dir'
    for address in L:
        url += '/' + address.replace(' ', '+')

    return url


if __name__ == "__main__":
    # get spread_sheet interface
    spread_sheet = get_gsheet(test_sheet=True)
    # get dict of address lists, worksheet values
    add_dict = read_address_sheets(spread_sheet)
    # optimize waypoint orders
    opt_dict = optimize_waypoints(add_dict)
    # links filename, then make links and write to file
    today = datetime.today()
    links_fname = 'links_' + '_'.join([str(today.day),
                                       str(today.month),
                                       str(today.year)]) + '.txt'
    process_routes(opt_dict, links_fname)
    # update cells in google sheets
    update_sheets(spread_sheet, opt_dict, sleep_time=0.05)
