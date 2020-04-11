import googlemaps as gm
import find_delivery_routes as fdr
import datetime

with open('google_cloud_api_key.txt', 'r') as f:
    API_KEY = f.readline().strip('\n')

gmc = gm.Client(key=API_KEY)

A, p = fdr.A, fdr.p

D, Ar, pr = fdr.make_distance_matrix(A, p)
R = fdr.find_routes(D, Ar, pr)
Ro = fdr.optimize_waypoints(R)
Rn = fdr.naive_find_routes(D, Ar, pr)
Rno = fdr.optimize_waypoints(Rn)
date = datetime.datetime.today()
date_list = [str(date.year), str(date.month), str(date.day),
             str(date.hour), str(date.minute)]
date_string = '_'.join(date_list)
S = fdr.make_directions_links(Ro, filename=date_string + '_routes.txt')
Sn = fdr.make_directions_links(Rno, filename=date_string + '_naive.txt')

