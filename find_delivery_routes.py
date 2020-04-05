import googlemaps as gm

with open('google_cloud_api_key.txt', 'r') as f:
    API_KEY = f.readline().strip('\n')

gmc = gm.Client(key=API_KEY)

# fixed/test set of addresses
A = ['1530 Haight St, San Francisco, CA 94117',  # Haight St Market
     '672 Stanyan St, San Francisco, CA 94117',  # Flywheel Coffee
     '1000 Cole St, San Francisco, CA 94117',  # La Boulangerie, Cole
     '1920 Hayes St #1126, San Francisco, CA 94117',  # Freewheel Bike Shop
     '397 Arguello Blvd, San Francisco, CA 94118',  # Arsicault Bakery
     '1300 Haight St, San Francisco, CA 94117',  # Ritual Coffee
     '815 Cole St, San Francisco, CA 94117',  # Ice Cream Bar
     '547 Haight St, San Francisco, CA 94117',  # Toronado
     '248 Church St, San Francisco, CA 94114',  # Thorough Bread
     '1331 9th Ave, San Francisco, CA 94122',  # Arizmendi Bakery
     '1224 9th Ave, San Francisco, CA 94122',  # Nopalito
     '4416 18th St, San Francisco, CA 94114',  # Mama Ji's
     '508 Castro St #32, San Francisco, CA 94114',  # Oz Pizza
     '554 Castro St, San Francisco, CA 94114',  # Castro Fountain
     '407 Castro St #2019, San Francisco, CA 94114',  # Hot Cookie
     '498 Sanchez St, San Francisco, CA 94114',  # La Marais
     '941 Cole St, San Francisco, CA 94117',  # Zazie
     '205A Frederick St, San Francisco, CA 94117',  # Bacon Bacon
     '2288 Mission St, San Francisco, CA 94110',  # Taqueria Cancun
     '600 Guerrero St, San Francisco, CA 94110',  # Tartine
     '3655 Lawton St, San Francisco, CA 94122']  # Andytown Coffee


def initialize_p_r():
    # TODO write this function for parsing
    #      pickup driver and fixed waypoint
    #      constraints from google sheet,
    #      encoding in p, r arrays

    # Arsicault, Toronado, Mama Ji's, Andytown
    p = [4, 7, 11, 20]

    r = [None for i in range(len(A))]
    pix = 0
    for i in p:
        r[i] = pix
        pix += 1
    return p, r


def make_distance_matrix(A):

    n_a = len(A)
    D = [[0 for i in range(n_a)] for j in range(n_a)]

    n_chunk = int(n_a/10)

    for ri in range(n_chunk+1):
        ra = ri*10
        if ri < n_chunk:
            rb = ri*10+10
        else:
            rb = n_a
        for ci in range(n_chunk+1):
            ca = ci*10
            if ci < n_chunk:
                cb = ci*10 + 10
            else:
                cb = n_a
            Dt = gmc.distance_matrix(origins=A[ra:rb],
                                     destinations=A[ca:cb],
                                     mode='driving')
            for ti, di in enumerate(range(ra, rb)):
                row = Dt['rows'][ti]
                for tj, dj in enumerate(range(ca, cb)):
                    D[di][dj] = row['elements'][tj]['distance']['value']
    return D


def sort_distance_matrix(D, origin_idx=0):
    dt = D[origin_idx]
    sidx = [i[0] for i in sorted(enumerate(dt), key=lambda x:x[1])]
    Ds = [[0 for i in range(len(dt))] for j in range(len(dt))]
    for i, j in enumerate(sidx):
        for k, l in enumerate(sidx):
            Ds[i][k] = D[j][l]
    return Ds, sidx


def find_routes(A, D, r, p):
    # the algorithm!
    return None, None
