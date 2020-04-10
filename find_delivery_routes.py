import googlemaps as gm
import read_google_sheet as rgs

with open('google_cloud_api_key.txt', 'r') as f:
    API_KEY = f.readline().strip('\n')

gmc = gm.Client(key=API_KEY)

# fixed/test set of addresses
A = [['Haight St Market', '1530 Haight St, San Francisco, CA 94117', None, 0],
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


def make_distance_matrix(A, p):

    n_a = len(A)
    n_chunk = int(n_a/100)

    D = [[0 for i in range(n_a)] for j in range(n_a)]

    for ci in range(n_chunk+1):
        ca = ci*100
        if ci < n_chunk:
            cb = ci*100+100
        else:
            cb = n_a
        dest_list = [A[cj][1] for cj in range(ca, cb)]
        Do = gmc.distance_matrix(origins=A[0][1],
                                 destinations=dest_list,
                                 mode='driving')
        row = Do['rows'][0]
        for ti, di in enumerate(range(ca, cb)):
            D[0][di] = row['elements'][ti]['distance']['value']

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
        Dr.append([0 for _ in range(n_a)])
        n_chunk = int((n_a-ii)/100)
        for ci in range(n_chunk+1):
            ca = ci*100+ii
            if ci < n_chunk:
                cb = ci*100+ii+100
            else:
                cb = n_a
            dest_list = [Ar[cj][1] for cj in range(ca, cb)]
            Do = gmc.distance_matrix(origins=a[1],
                                     destinations=dest_list,
                                     mode='driving')
            row = Do['rows'][0]
            for ti, di in enumerate(range(ca, cb)):
                Dr[ii][di] = row['elements'][ti]['distance']['value']

    return Dr, Ar, pr


def find_routes(A, D, p):
    # the algorithm!
    return None, None
