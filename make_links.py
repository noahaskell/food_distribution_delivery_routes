import pandas as pd
from urllib.parse import urlencode


def process_routes(in_file='routes_temp.csv', out_file='links.txt'):
    df = pd.read_csv(in_file)
    routes = df['route'].unique()
    all_routes = {}
    cols = ['street', 'city', 'zip']
    for name in routes:
        rows = df.loc[df['route'] == name].index
        this_route = []
        for row in rows:
            list_temp = [str(x) for x in list(df.loc[row, cols])]
            this_route.append(' '.join(list_temp))
        lenny = len(this_route)
        if lenny <= 11:
            link = make_directions_link(this_route)
            all_routes[name] = link
        else:
            a = 0
            b = min(a+11, lenny)
            ri = 0
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


def make_directions_link(L, filename=None):
    base_url = 'https://www.google.com/maps/dir/?api=1&'
    url_dict = {}
    url_dict['origin'] = L[0]
    url_dict['destination'] = L[-1]
    url_dict['waypoints'] = '|'.join(L[1:-1])
    url_dict['travelmode'] = 'driving'

    return base_url + urlencode(url_dict)


if __name__ == '__main__':
    process_routes()
