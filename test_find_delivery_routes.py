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
        r = [None, None, None, None, 0, 1]
        p = [4, 5]
        Dc = [[0, 316, 589, 784, 803, 2384],
              [0, 0, 1001, 1103, 1368, 2810],
              [0, 0, 0, 853, 914, 1794],
              [0, 0, 0, 0, 1767, 2674]]
        Dt = fdr.make_distance_matrix(As, p, r)
        self.assertEqual(Dc, Dt)

    def test_sort_distance_matrix(self):
        As = fdr.A[:3]
        Ar = [As[0], As[2], As[1]]
        Do = [[0, 784, 589],
              [784, 0, 853],
              [589, 853, 0]]
        Ds = [[0, 589, 784],
              [589, 0, 853],
              [784, 853, 0]]
        Dr = fdr.make_distance_matrix(Ar)
        Dt, sidx = fdr.sort_distance_matrix(Dr)
        self.assertEqual(Ds, Dt)
        self.assertEqual(Do, Dr)

    def test_find_routes(self):
        A = fdr.A[:5]
        D = fdr.make_distance_matrix(A)
        p = [1, 4]
        r = [None, 0, None, None, 1]
        S, C = fdr.find_routes(A, D, r, p)
