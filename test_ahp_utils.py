import unittest
import numpy as np
from ahp_utils import calculate_weights

class TestCalculateWeights(unittest.TestCase):
    def test_valid_matrix(self):
        matrix = np.array([[1, 2], [0.5, 1]])
        weights, CR = calculate_weights(matrix)
        self.assertAlmostEqual(sum(weights), 1.0)
        self.assertLessEqual(CR, 0.1)

    def test_invalid_matrix(self):
        matrix = np.array([[1, 2], [3, 1]])
        with self.assertRaises(ValueError):
            calculate_weights(matrix)

if __name__ == "__main__":
    unittest.main()