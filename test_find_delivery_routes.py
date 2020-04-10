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
        self.assertIsInstance(data, dict)
        headers = ['Name', 'Street address', 'Apt / Unit #', 'City, State',
                   'Zip code', 'Pick-up or Delivery', 'Driver']
        self.assertTrue(data['valueRanges'][0]['values'][0]==headers)

    def test_make_address_list(self):
        with open('google_sheet_id.txt', 'r') as f:
           sheet_id = f.readline().strip('\n')
        data_range = 'A1:G100'
        dd = rgs.read_sheet(sheet_id, data_range)
        dl = dd['valueRanges'][0]['values']
        add_list, p_list = rgs.make_address_list(dl)
        self.assertTrue(all([isinstance(i, list) for i in add_list]))
        origin_address = '7941 Elizabeth Street, Mount Healthy, OH, 45231'
        self.assertTrue(add_list[0][1] == origin_address)

class TestFindRoutes(unittest.TestCase):

    def test_make_distance_matrix(self):
        As = [['Haight St Market', '1530 Haight St, San Francisco, CA 94117', None, 0],
              ['Flywheel', '672 Stanyan St, San Francisco, CA 94117', 'Arsicault', 0],
              ['La Boulangerie', '1000 Cole St, San Francisco, CA 94117', None, 1],
              ['Freewheel Bike Shop', '1920 Hayes St #1126, San Francisco, CA 94117', None, 0],
              ['Arsicault', '397 Arguello Blvd, San Francisco, CA 94118', None, 1], 
              ['Ritual Coffee', '1300 Haight St, San Francisco, CA 94117', 'La Boulangerie', 0]]
        At = [As[0], As[5], As[1], As[3], As[4], As[2]]
        p = [2, 4]
        Dc = [[0, 316, 589, 803, 2384, 784],
              [0, 0, 1001, 1368, 2810, 1103],
              [0, 0, 0, 914, 1794, 853],
              [0, 0, 0, 0, 1981, 1577]]
        Dr, Ar, pr = fdr.make_distance_matrix(As, p)
        self.assertEqual(At, Ar)
        self.assertEqual([4, 5], pr)
        self.assertEqual(Dc[0], Dr[0])

    def _test_find_routes(self):
        A = fdr.A[:5]
        D = fdr.make_distance_matrix(A)
        p = [1, 4]
        r = [None, 0, None, None, 1]
        S, C = fdr.find_routes(A, D, r, p)
