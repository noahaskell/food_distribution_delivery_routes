import unittest
import sys
import find_delivery_routes as fdr
import read_google_sheet as rgs


class TestReadSheet(unittest.TestCase):

    # from https://stackoverflow.com/a/56381855/3297752
    def setUp(self):
        if not sys.warnoptions:
            import warnings
            warnings.simplefilter("ignore")

    def test_read_sheet(self):
        with open('google_sheet_id.txt', 'r') as f:
           sheet_id = f.readline().strip('\n')
        data_range = 'A1:G100'
        data = rgs.read_sheet(sheet_id, data_range)
        self.assertIsInstance(data, list)
        headers = ['Name', 'Street address', 'Apt / Unit #', 'City, State',
                   'Zip code', 'Pick-up or Delivery', 'Driver']
        self.assertTrue(data[0]==headers)

    def test_make_address_list(self):
        with open('google_sheet_id.txt', 'r') as f:
           sheet_id = f.readline().strip('\n')
        data_range = 'A1:G1000'
        dl = rgs.read_sheet(sheet_id, data_range)
        add_list, p_list = rgs.make_address_list(dl)
        self.assertTrue(all([isinstance(i, list) for i in add_list]))
        origin_address = '7941 Elizabeth Street, Mount Healthy, OH, 45231'

        self.assertTrue(add_list[0][1] == origin_address)

class TestFindRoutes(unittest.TestCase):

    def setUp(self):
        self.As = [['Haight St Market', '1530 Haight St, San Francisco, CA 94117', None, 0],
                   ['Flywheel', '672 Stanyan St, San Francisco, CA 94117', 'Arsicault', 0],
                   ['La Boulangerie', '1000 Cole St, San Francisco, CA 94117', None, 1],
                   ['Freewheel Bike Shop', '1920 Hayes St #1126, San Francisco, CA 94117', None, 0],
                   ['Arsicault', '397 Arguello Blvd, San Francisco, CA 94118', None, 1], 
                   ['Ritual Coffee', '1300 Haight St, San Francisco, CA 94117', 'La Boulangerie', 0]]
        self.At = [self.As[0], self.As[5], self.As[1], self.As[3], self.As[4], self.As[2]]
        self.p = [2, 4]
        self.Dc = [[0, 316, 589, 803, 2384, 784],
                   [0, 0, 1001, 1368, 2810, 1103],
                   [0, 0, 0, 914, 1794, 853],
                   [0, 0, 0, 0, 1981, 1577]]
        self.Dr = [self.Dc[0][0], self.Dc[0][2], self.Dc[0][5],
                   self.Dc[0][3], self.Dc[0][4], self.Dc[0][1]]  

    def test_make_distance_row(self):
        Dr = fdr.make_distance_row(self.As)
        self.assertEqual(self.Dr, Dr)

    def test_make_distance_matrix(self):
        Dr, Ar, pr = fdr.make_distance_matrix(self.As, self.p)
        self.assertEqual(self.At, Ar)
        self.assertEqual([4, 5], pr)
        self.assertEqual(self.Dc[0], Dr[0])

    def test_find_routes(self):
        D, Ar, pr  = fdr.make_distance_matrix(self.As, self.p)
        R = fdr.find_routes(D, Ar, pr)
        self.assertIsInstance(R, dict)
        # make more tests?

    def test_naive_find_routes(self):
        D, Ar, pr  = fdr.make_distance_matrix(self.As, self.p)
        R = fdr.naive_find_routes(D, Ar, pr)
        self.assertIsInstance(R, dict)
        # make more tests?
        

    def test_make_directions_links(self):
        D, Ar, pr  = fdr.make_distance_matrix(self.As, self.p)
        R = fdr.find_routes(D, Ar, pr)
        S = fdr.make_directions_links(R)
        self.assertIsInstance(S, dict)
        self.assertTrue(all([v[1].split('\n')[0] == self.As[0][0]\
                            + ' ' + self.As[0][1] for v in S.values()]))

