import googlemaps as gm
import read_google_sheet as rgs
import datetime
from urllib.parse import urlencode
from array import array


def get_maps_client(key_file='google_cloud_api_key.txt'):
    """
    Creates and returns Google Maps client.
    """
    with open(key_file, 'r') as f:
        API_KEY = f.readline().strip('\n')

    return gm.Client(key=API_KEY)


def fixed_addresses():
    """
    Fixed list of address tuples

    :returns: list of address tuples A
    :returns: array of driver indices p
    """

    A = [('Haight St Market',
          '1530 Haight St, San Francisco, CA 94117', None, -1),
         ('Flywheel',
          '672 Stanyan St, San Francisco, CA 94117', None, 0),
         ('La Boulangerie',
          '1000 Cole St, San Francisco, CA 94117', None, 1),
         ('Freewheel Bike Shop',
          '1920 Hayes St #1126, San Francisco, CA 94117', 'Arsicault', 0),
         ('Arsicault',
          '397 Arguello Blvd, San Francisco, CA 94118', None, 1),
         ('Ritual Coffee',
          '1300 Haight St, San Francisco, CA 94117', 'Boulangerie', 0),
         ('Ice Cream Bar',
          '815 Cole St, San Francisco, CA 94117', None, 0),
         ('Toronado',
          '547 Haight St, San Francisco, CA 94117', None, 1),
         ('Thorough Bread',
          '248 Church St, San Francisco, CA 94114', None, 0),
         ('Arizmendi',
          '1331 9th Ave, San Francisco, CA 94122', 'Andytown', 0),
         ('Nopalito',
          '1224 9th Ave, San Francisco, CA 94122', None, 0),
         ('Mama Jis',
          '4416 18th St, San Francisco, CA 94114', None, 1),
         ('Oz Pizza',
          '508 Castro St #32, San Francisco, CA 94114', None, 0),
         ('Castro Fountain',
          '554 Castro St, San Francisco, CA 94114', None, 0),
         ('Hot Cookie',
          '407 Castro St #2019, San Francisco, CA 94114', 'Mama', 0),
         ('La Marais',
          '498 Sanchez St, San Francisco, CA 94114', None, 0),
         ('Zazie',
          '941 Cole St, San Francisco, CA 94117', None, 0),
         ('Bacon Bacon',
          '205A Frederick St, San Francisco, CA 94117', None, 0),
         ('Taqueria Cancun',
          '2288 Mission St, San Francisco, CA 94110', None, 0),
         ('Tartine',
          '600 Guerrero St, San Francisco, CA 94110', None, 0),
         ('Andytown',
          '3655 Lawton St, San Francisco, CA 94122', None, 1)]

    p = array('i', [i for i, a in enumerate(A) if a[-1] == 1])

    return A, p


def make_distance_row(A, gmc, o_idx=0, offset=0):
    n_a = len(A)
    chunk_size = 100  # google maps only returns 100 distances per request
    n_chunk = int((n_a-offset-1)/chunk_size)

    D = array('i', [0 for i in range(n_a)])

    for ci in range(n_chunk+1):
        ca = ci*chunk_size+offset  # start index for chunk ci
        if ci < n_chunk:
            cb = ci*chunk_size+chunk_size+offset  # end index
        else:
            cb = n_a  # end index
        dest_list = [A[cj][1] for cj in range(ca, cb)]
        Do = gmc.distance_matrix(origins=A[o_idx][1],
                                 destinations=dest_list,
                                 mode='driving')
        row = Do['rows'][0]
        for ti, di in enumerate(range(ca, cb)):
            D[di] = row['elements'][ti]['distance']['value']
    return D


def make_distance_matrix(A, p, gmc, full_matrix=False):

    n_a = len(A)

    D = make_distance_row(A, gmc)

    n_p = len(p)
    n_w = n_a - n_p  # number of waypoints
    Ap = [A.pop(i) for i in p[::-1]]
    Dp = array('i', [D.pop(i) for i in p[::-1]])

    sidx = [i[0] for i in sorted(enumerate(D), key=lambda x: x[1])]
    Ar = [A[i] for i in sidx] + Ap
    pr = list(range(n_a-n_p, n_a))
    Dr = [array('i', [D[i] for i in sidx]) + Dp]

    for i, a in enumerate(Ar[1:n_w]):
        if full_matrix:
            offset = 0
        else:
            offset = i+2
        Dr.append(make_distance_row(Ar, gmc, o_idx=i+1, offset=offset))

    return Dr, Ar, pr


def find_routes(D, A, p):
    R = {}
    d_offset = p[0]
    n_driver = len(p)
    for i, di in enumerate(p):
        R[i] = {}
        R[i]['name'] = A[di][0] # driver name
        R[i]['route_address'] = [A[0][:2]] # route address list w/ origin
        R[i]['route_idx'] = [0] # route indices for querying D w/ origin
        R[i]['distance'] = 0 # total distance of route

    for i, a in enumerate(A):
        if i not in p and i != 0:
            if a[2] is not None: # pre-designated driver
                found_driver = False
                for j in range(n_driver):
                    if a[2] in R[j]['name']:
                        found_driver = True
                        R[j]['route_address'].append(a)
                        R[j]['distance'] += D[R[j]['route_idx'][-1]][i]
                        R[j]['route_idx'].append(i)
                if not found_driver:
                    print('Failed to find pre-designated driver ' + a[2] + ' for ' + a[0])
            else:
                j_min, d_min = -1, 1e6
                for j in range(n_driver):
                    this_distance = D[R[j]['route_idx'][-1]][i] + D[i][p[j]]
                    if this_distance < d_min:
                        j_min, d_min = j, this_distance
                R[j_min]['route_address'].append(a[:2])
                R[j_min]['route_idx'].append(i)
                R[j_min]['distance'] += d_min - D[i][p[j]]
    for j, di in enumerate(p):
        R[j]['route_address'].append(A[di][:2])
        R[j]['distance'] += D[R[j]['route_idx'][-1]][di]
        R[j]['route_idx'].append(di)
    return R


def naive_find_routes(D, A, p):
    R = {}
    d_offset = p[0]
    n_driver = len(p)
    for i, di in enumerate(p):
        R[i] = {}
        R[i]['name'] = A[di][0] # driver name
        R[i]['route_address'] = [A[0][:2]] # route address list w/ origin
        R[i]['route_idx'] = [0] # route indices for querying D w/ origin
        R[i]['distance'] = 0 # total distance of route

    for i, a in enumerate(A):
        if i not in p and i != 0:
            if a[2] is not None: # pre-designated driver
                found_driver = False
                for j in range(n_driver):
                    if a[2] in R[j]['name']:
                        found_driver = True
                        R[j]['route_address'].append(a)
                        R[j]['distance'] += D[R[j]['route_idx'][-1]][i]
                        R[j]['route_idx'].append(i)
                if not found_driver:
                    print('Failed to find pre-designated driver ' + a[2] + ' for ' + a[0])
            else:
                j_min, d_min = -1, 1e6
                for j in range(n_driver):
                    if D[0][i] + D[i][p[j]] < d_min:
                        j_min, d_min = j, D[0][i] + D[i][p[j]]
                R[j_min]['route_address'].append(a[:2])
                R[j_min]['distance'] += D[R[j]['route_idx'][-1]][i]
                R[j_min]['route_idx'].append(i)
    for j, di in enumerate(p):
        R[j]['route_address'].append(A[di][:2])
        R[j]['distance'] += D[R[j]['route_idx'][-1]][di]
        R[j]['route_idx'].append(di)
    return R


def make_directions_links(R, filename=None):
    base_url = 'https://www.google.com/maps/dir/?api=1&'
    link_dict = {}
    for k, v in R.items():
        url_dict = {}
        url_dict['origin'] = v['route_address'][0][1]
        url_dict['destination'] = v['route_address'][-1][1]
        url_dict['waypoints'] = '|'.join([a[1] for a in v['route_address'][1:-1]])
        url_dict['travelmode'] = 'driving'
        link_dict[v['name']] = []
        link_dict[v['name']].append(base_url + urlencode(url_dict))
        link_dict[v['name']].append('\n'.join([a[0] + ' ' + a[1] for a in v['route_address']]))

    if filename is not None:
        with open(filename, 'w') as f:
            for k, v in link_dict.items():
                f.write(k + '\n')
                f.write(v[0] + '\n')
                f.write(v[1] + '\n')
                f.write('\n')
    return link_dict


def read_address_gsheet(id_file='google_sheet_id.txt'):
    with open(id_file, 'r') as f:
        sheet_id = f.readline().strip('\n')
    data_range = 'A1:G1000'
    gs_list = rgs.read_sheet(sheet_id, data_range)
    address_list, driver_idx_list = rgs.make_address_list(gs_list)
    return address_list, driver_idx_list

if __name__ == '__main__':
    D, Ar, pr = make_distance_matrix(add_list, di_list)
    R = find_routes(D, Ar, pr)
    Rn = naive_find_routes(D, Ar, pr)
    date = datetime.datetime.today()
    date_list = [str(date.year), str(date.month), str(date.day),
                 str(date.hour), str(date.minute)]
    date_string = '_'.join(date_list)
    S = make_directions_links(R, filename=date_string + '_routes.txt')
    Sn = make_directions_links(Rn, filename=date_string + '_naive.txt')
