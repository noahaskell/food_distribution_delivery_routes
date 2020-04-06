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


def make_distance_matrix(A, p, r):

    n_a = len(A)
    n_chunk = int(n_a/100)

    D = [[0 for i in range(n_a)] for j in range(n_a)]

    for ci in range(n_chunk+1):
        ca = ci*100
        if ci < n_chunk:
            cb = ci*100+100
        else:
            cb = n_a
        Do = gmc.distance_matrix(origins=A[0],
                                 destinations=A[ca:cb],
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
    rr = [None for i in range(n_a-n_p)] + list(range(n_p))
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
            Do = gmc.distance_matrix(origins=a,
                                     destinations=Ar[ii:],
                                     mode='driving')
            row = Do['rows'][0]
            for ti, di in enumerate(range(ca, cb)):
                Dr[ii][di] = row['elements'][ti]['distance']['value']

    return Dr, Ar, pr, rr


def find_routes(A, D, r, p):
    # the algorithm!
    return None, None
