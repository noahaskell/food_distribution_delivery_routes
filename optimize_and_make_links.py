import pickle
import os
import configparser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googlemaps as gm
from datetime import datetime
from urllib.parse import urlencode


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def get_maps_client(key_file='google_cloud_api_key.txt'):
    """
    Creates and returns Google Maps client.
    """
    with open(key_file, 'r') as f:
        API_KEY = f.readline().strip('\n')

    return gm.Client(key=API_KEY)


def sheet_service():
    """
    Boilerplate code for connecting to google sheets

    Returns service object
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    return service


def read_address_sheets(service, data_range=None, test_sheet=False):
    """
    Reads and parses addresses from sheets with titles like "[Name] ~ List"

    Parameters
    ----------
    service : google api client resource (returned by sheet_service())
        connection to google sheets
    data_range : str
        indicates ranges of cells of interest (e.g., "A1:J20")
    test_sheet : bool
        True if test sheet should be used, else False

    Returns
    -------
    dict
        keys = driver names, values = lists of addresses
        list of addresses = [origin, waypoints, destination]
    """

    config = configparser.ConfigParser()
    config.read('google_sheet_id.txt')
    if test_sheet:
        sheet_id = config['test']
    else:
        sheet_id = config['real']

    if data_range is None:
        data_range = 'A1:J100'

    sheet_metadata = (service
                      .spreadsheets()
                      .get(spreadsheetId=sheet_id)
                      .execute())
    sheets = sheet_metadata.get('sheets', '')
    sheet_id_list = []
    for sh in sheets:
        props = sh.get('properties')
        title = props.get('title')
        if '~ List' in title and 'Self' not in title:
            sheet_id_list.append(title)

    sheet = service.spreadsheets()
    values_dict = {}
    for title in sheet_id_list:
        range_t = title + '!' + data_range
        result = sheet.values().batchGet(spreadsheetId=sheet_id,
                                         ranges=range_t).execute()
        add_list_t = make_address_list(result['valueRanges'][0]['values'])
        name = title.split('~')[0].strip()
        values_dict[name] = add_list_t

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
        this_add = ' '.join([street, city_state, zip_code])
        add_list.append(this_add)
        if 'Driver' in this_list[-1]:
            break

    return add_list


def optimize_waypoints(add_dict, gmap_client):
    """
    Uses google maps api to optimize waypoints for routes

    Parameters
    ----------
    add_dict : dict
        dictionary with name: addres_list items
    gmap_client : google maps client
        returned by get_maps_client()

    Returns
    -------
    dict
        dictionary with name: optimized route list items
    """

    opt_dict = {}
    for name, add_list in add_dict.items():
        origin = add_list[0]
        destin = add_list[-1]
        waypts = add_list[1:-1]
        opt_list = gmap_client.directions(origin=origin,
                                          destination=destin,
                                          waypoints=waypts,
                                          mode='driving',
                                          optimize_waypoints=True)
        opt_idx = opt_list[0]['waypoint_order']
        opt_route = [origin]
        for i in opt_idx:
            opt_route.append(add_list[i+1])
        opt_route.append(destin)
        opt_dict[name] = opt_route
    return opt_dict


def process_routes(address_dict, out_file='links.txt'):
    """
    Makes clickable google map directions links from address lists;
     for routes with 12+ addresses, splits into parts of 11 or fewer

    Parameters
    ----------
    address_dict : dict
        dictionary of name: route list items
    out_file : str
        string specifying filename for name: link dump

    Returns
    -------
    dict
        if out_file is None, dict with (split) name: route items
    """

    all_routes = {}
    for name, this_route in address_dict.items():
        lenny = len(this_route)
        if lenny <= 11:
            link = make_directions_link(this_route)
            all_routes[name] = link
        else:
            a = 0
            b = min(a+11, lenny)
            ri = 1
            while a < lenny and b <= lenny:
                route_sublist = this_route[a:b]
                if len(route_sublist) > 0:
                    link = make_directions_link(route_sublist)
                    all_routes[name + ' ' + str(ri)] = link
                a += 10
                b = min(a+11, lenny)
                ri += 1

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

    base_url = 'https://www.google.com/maps/dir/?api=1&'
    url_dict = {}
    url_dict['origin'] = L[0]
    url_dict['destination'] = L[-1]
    url_dict['waypoints'] = '|'.join(L[1:-1])
    url_dict['travelmode'] = 'driving'

    return base_url + urlencode(url_dict)


if __name__ == "__main__":
    gmc = get_maps_client()  # google maps client
    service = sheet_service()  # sheet service object
    # name: address list items
    add_dict = read_address_sheets(service=service,
                                   gsheet_fname='google_sheet_id.txt',
                                   data_range='A1:J50')
    # wth optimized waypoints
    opt_dict = optimize_waypoints(add_dict=add_dict,
                                  gmap_client=gmc)
    # links filename, then make links and write to file
    today = datetime.today()
    links_fname = 'links_' + '_'.join([str(today.day),
                                       str(today.month),
                                       str(today.year)]) + '.txt'
    process_routes(opt_dict, links_fname)
