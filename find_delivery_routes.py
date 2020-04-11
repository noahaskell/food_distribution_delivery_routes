import googlemaps as gm
import read_google_sheet as rgs

with open('google_cloud_api_key.txt', 'r') as f:
    API_KEY = f.readline().strip('\n')

gmc = gm.Client(key=API_KEY)

# fixed/test set of addresses
A = [['Haight St Market', '1530 Haight St, San Francisco, CA 94117', None, -1],
     ['Flywheel', '672 Stanyan St, San Francisco, CA 94117', 'Andytown', 0],
     ['La Boulangerie', '1000 Cole St, San Francisco, CA 94117', None, 0],
     ['Freewheel Bike Shop', '1920 Hayes St #1126, San Francisco, CA 94117', None, 0],
     ['Arsicault', '397 Arguello Blvd, San Francisco, CA 94118', None, 1], 
     ['Ritual Coffee', '1300 Haight St, San Francisco, CA 94117', 'Toronado', 0],
     ['Ice Cream Bar', '815 Cole St, San Francisco, CA 94117', None, 0],
     ['Toronado', '547 Haight St, San Francisco, CA 94117', None, 1],
     ['Thorough Bread', '248 Church St, San Francisco, CA 94114', None, 0],
     ['Arizmendi', '1331 9th Ave, San Francisco, CA 94122', 'Andytown', 0],
     ['Nopalito', '1224 9th Ave, San Francisco, CA 94122', None, 0],
     ['Mama Jis', '4416 18th St, San Francisco, CA 94114', None, 1],
     ['Oz Pizza', '508 Castro St #32, San Francisco, CA 94114', None, 0],
     ['Castro Fountain', '554 Castro St, San Francisco, CA 94114', None, 0],
     ['Hot Cookie', '407 Castro St #2019, San Francisco, CA 94114', 'Mama', 0],
     ['La Marais', '498 Sanchez St, San Francisco, CA 94114', None, 0],
     ['Zazie', '941 Cole St, San Francisco, CA 94117', None, 0],
     ['Bacon Bacon', '205A Frederick St, San Francisco, CA 94117', None, 0],
     ['Taqueria Cancun', '2288 Mission St, San Francisco, CA 94110', None, 0],
     ['Tartine', '600 Guerrero St, San Francisco, CA 94110', None, 0],
     ['Andytown', '3655 Lawton St, San Francisco, CA 94122', None, 1]]

p = [i for i, a in enumerate(A) if a[-1]==1]


def make_distance_row(A, o_idx=0, offset=0):
    n_a = len(A)
    n_chunk = int((n_a-offset)/100)

    D = [0 for i in range(n_a)]

    for ci in range(n_chunk+1):
        ca = ci*100
        if ci < n_chunk:
            cb = ci*100+100+offset
        else:
            cb = n_a
        dest_list = [A[cj][1] for cj in range(ca, cb)]
        Do = gmc.distance_matrix(origins=A[o_idx][1],
                                 destinations=dest_list,
                                 mode='driving')
        row = Do['rows'][0]
        for ti, di in enumerate(range(ca, cb)):
            D[di] = row['elements'][ti]['distance']['value']
    return D


def make_distance_matrix(A, p):

    n_a = len(A)

    D = []
    D.append(make_distance_row(A))

    n_p = len(p)
    n_w = n_a - n_p
    Ap = [A.pop(i) for i in p[::-1]]
    Dp = [D[0].pop(i) for i in p[::-1]]

    sidx = [i[0] for i in sorted(enumerate(D[0]), key=lambda x:x[1])]
    Ar = [A[i] for i in sidx] + Ap
    pr = list(range(n_a-n_p, n_a))
    Dr = [[D[0][i] for i in sidx] + Dp]

    for i, a in enumerate(Ar[1:n_w]):
        ii = i + 1
        Dr.append(make_distance_row(Ar, o_idx=i, offset=ii))

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
            #if a[2] not None: # pre-designated driver
            #    for di in range(n_driver):
            #        if a[2] in R[di]['name']:
            #            R[di]['route_address'].append(a)
            #            R[di]['distance'] += D[R[di]['route_idx'][-1]][i]
            #            R[di]['route_idx'].append(i)
            #else:
            j_min, d_min = -1, 1e6
            for j in range(n_driver):
                if D[R[j]['route_idx'][-1]][i] + D[i][p[j]] < d_min:
                    j_min, d_min = j, D[R[j]['route_idx'][-1]][i]
            R[j_min]['route_address'].append(a[:2])
            R[j_min]['route_idx'].append(i)
            R[j_min]['distance'] += d_min
    for j, di in enumerate(p):
        R[j]['route_address'].append(A[di][:2])
        R[j]['distance'] += D[R[j]['route_idx'][-1]][di]
        R[j]['route_idx'].append(di)
    return R
