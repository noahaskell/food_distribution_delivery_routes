import unittest
import find_delivery_routes as fdr


class TestFindRoutes(unittest.TestCase):

    def test_initialize_p_r(self):
        A = fdr.A
        # Arsicault, Toronado, Mama Ji's, Andytown
        p = [4, 7, 11, 20]

        r = [None for i in range(len(A))]
        pix = 0
        for i in p:
            r[i] = pix
            pix += 1
        pt, rt = fdr.initialize_p_r()
        self.assertEqual(pt, p)
        self.assertEqual(rt, r)

    def test_make_distance_matrix(self):
        As = fdr.A[:6]
        At = [As[0], As[5], As[1], As[3], As[4], As[2]]
        r = [None, None, 0, None, 1, None]
        p = [2, 4]
        Dc = [[0, 316, 589, 803, 2384, 784],
              [0, 0, 1001, 1368, 2810, 1103],
              [0, 0, 0, 914, 1794, 853],
              [0, 0, 0, 0, 1981, 1577]]
        Dr, Ar, pr, rr = fdr.make_distance_matrix(As, p, r)
        self.assertEqual(At, Ar)
        self.assertEqual([4, 5], pr)
        rt = [None, None, None, None, 0, 1]
        self.assertEqual(rt, rr)
        self.assertEqual(Dc[0], Dr[0])

    def _test_find_routes(self):
        A = fdr.A[:5]
        D = fdr.make_distance_matrix(A)
        p = [1, 4]
        r = [None, 0, None, None, 1]
        S, C = fdr.find_routes(A, D, r, p)
