import unittest
from src.module_1.module_1_meteo_api import process_data


class TestProcessData(unittest.TestCase):
    def runTest(self):
        data = {
            "time": ["2021-01-01", "2021-01-02"],
            "temperature_2m_mean": [10, 20],
            "precipitation_sum": [0, 5],
            "soil_moisture_0_to_10cm_mean": [0.5, 0.6],
        }
        processed_data = process_data(data)
        self.assertEqual(len(processed_data), 3)
