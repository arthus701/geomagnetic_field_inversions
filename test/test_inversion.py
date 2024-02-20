import unittest
from pathlib import Path

import numpy as np
from pandas import read_csv

from geomagnetic_field_inversions.data_prep import InputData
from geomagnetic_field_inversions import FieldInversion

path = Path(__file__).parent

with open(path / '../benchmark_data/newmod', 'r') as fh:
    t_min, t_max = map(float, fh.readline().split()[0:2])
    # read the rest as a long string
    input_string = ' '.join(fh.readlines())
    # create an array from the string
    input_array = np.fromstring(input_string, dtype=float, sep=' ')
    # get the relevant quantities from the array
    l_max, n_spl = map(int, input_array[:2])
    # read the appropriate number of knots
    knots = input_array[2:n_spl+4+2]
    # read the appropriate number of coefficients
    n_coeffs = l_max * (l_max + 2)
    ref_coeffs = input_array[n_spl+4+2:n_spl*(n_coeffs+1)+4+2]
    ref_coeffs = ref_coeffs.reshape(n_spl, n_coeffs)

raw_data = read_csv(path / '../benchmark_data/testdata.csv')
raw_data = raw_data.query(f'{t_min} <= t <= {t_max}')
raw_data.reset_index(inplace=True, drop=True)

raw_data.loc[:, 'D'] /= 10
raw_data.loc[:, 'dD'] /= 10
raw_data.loc[:, 'I'] /= 10
raw_data.loc[:, 'dI'] /= 10

iData = InputData()
iData.read_data(raw_data)
iData.compile_data()


class Test_inversion(unittest.TestCase):
    def test_single_inversion(self):
        lambda_s = 1.0e-13
        lambda_t = 1.0e-3

        fInv = FieldInversion(
            t_min=t_min, t_max=t_max, t_step=knots[1]-knots[0],
            maxdegree=10,
            verbose=False,
        )

        fInv.prepare_inversion(
            iData,
            spat_type="ohmic_heating",
            temp_type="min_acc",
        )

        x0 = np.zeros(fInv._nm_total)
        x0[0] = -30e3
        fInv.run_inversion(
            x0,
            max_iter=0,
            spat_damp=lambda_s,
            temp_damp=lambda_t,
        )

        res_coeffs = fInv.splined_gh

        # for it in range(res_coeffs.shape[1]):
        #     abserr = np.abs(res_coeffs[:, it] - ref_coeffs[:, it])
        #     relerr = np.abs(abserr / ref_coeffs[:, it])
        #     print(it+1, np.max(abserr), np.max(relerr))

        # from matplotlib import pyplot as plt
        # ind = 1
        # plt.plot(
        #     knots[2:-2],
        #     ref_coeffs[:, ind],
        # )
        # plt.plot(
        #     knots[2:-2],
        #     res_coeffs[:, ind],
        # )
        # plt.show()

        self.assertTrue(
            np.allclose(
                ref_coeffs,
                res_coeffs,
                rtol=5e-3,
                atol=10,
            )
        )


if __name__ == '__main__':
    unittest.main()