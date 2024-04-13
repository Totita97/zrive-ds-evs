import unittest
from src.module_1.module_1_meteo_api import process_data, validate_response_schema
import pandas as pd


class TestProcessData(unittest.TestCase):
    def runTest(self):
        data = {
            "time": ["2021-01-01", "2021-01-01", "2021-01-02", "2021-01-02"],
            "temperature_2m_mean": [10, 15, 28, 20],
            "precipitation_sum": [0, 5, 2, 9],
            "soil_moisture_0_to_10cm_mean": [0.5, 0.2, 0.7, 0.6],
        }

        processed_data = process_data(data)

        # Verify that the length of processed data is 3
        self.assertEqual(len(processed_data), 3)

        # Check specific content of the data frames
        self.assertIn("temperature_2m_mean", processed_data)
        self.assertIn("precipitation_sum", processed_data)
        self.assertIn("soil_moisture_0_to_10cm_mean", processed_data)

        # Check the content of the temperature data frame
        temperature_df = processed_data["temperature_2m_mean"]
        self.assertIsInstance(temperature_df, pd.DataFrame)
        self.assertEqual(temperature_df["mean"].tolist(), [12.5, 24])
        self.assertEqual(temperature_df["std"].tolist(), [3.5355, 5.6569])

        # Check the content of the precipitation data frame
        precipitation_df = processed_data["precipitation_sum"]
        self.assertIsInstance(precipitation_df, pd.DataFrame)
        self.assertEqual(precipitation_df["mean"].tolist(), [2.5, 5.5])
        self.assertEqual(precipitation_df["std"].tolist(), [3.5355, 4.9497])

        # Check the content of the soil moisture data frame
        soil_moisture_df = processed_data["soil_moisture_0_to_10cm_mean"]
        self.assertIsInstance(soil_moisture_df, pd.DataFrame)
        self.assertEqual(soil_moisture_df["mean"].tolist(), [0.35, 0.65])
        self.assertEqual(soil_moisture_df["std"].tolist(), [0.2121, 0.0707])


class TestValidateResponseSchema(unittest.TestCase):
    def test_valid_data(self):
        data = {
            "daily": {
                "time": ["2021-01-01", "2021-01-02"],
                "temperature_2m_mean": [10, 20],
                "precipitation_sum": [5, 10],
                "soil_moisture_0_to_10cm_mean": [0.5, 0.6],
            }
        }

        validate_response_schema(data)

    def test_missing_daily(self):
        data = {}
        with self.assertRaises(Exception) as context:
            validate_response_schema(data)
        self.assertIn("Daily data not found in response", str(context.exception))

    def test_missing_variable(self):
        data = {
            "daily": {
                "time": ["2021-01-01", "2021-01-02"],
                "temperature_2m_mean": [10, 20],
                "precipitation_sum": [5, 10]
                # Missing soil_moisture_0_to_10cm_mean
            }
        }
        with self.assertRaises(Exception) as context:
            validate_response_schema(data)
        self.assertIn(
            "Variable soil_moisture_0_to_10cm_mean not found in response",
            str(context.exception),
        )

    def test_missing_time(self):
        data = {
            "daily": {
                "temperature_2m_mean": [10, 20],
                "precipitation_sum": [5, 10],
                "soil_moisture_0_to_10cm_mean": [0.5, 0.6],
            }
        }
        with self.assertRaises(Exception) as context:
            validate_response_schema(data)
        self.assertIn("Time data not found in response", str(context.exception))

    def test_empty_data(self):
        data = {
            "daily": {
                "time": [],
                "temperature_2m_mean": [],
                "precipitation_sum": [],
                "soil_moisture_0_to_10cm_mean": [],
            }
        }
        with self.assertRaises(Exception) as context:
            validate_response_schema(data)
        self.assertIn("No time data found in response", str(context.exception))

    def test_data_length_mismatch(self):
        data = {
            "daily": {
                "time": ["2021-01-01", "2021-01-02"],
                "temperature_2m_mean": [10],  # Length mismatch
                "precipitation_sum": [5, 10],
                "soil_moisture_0_to_10cm_mean": [0.5, 0.6],
            }
        }
        with self.assertRaises(Exception) as context:
            validate_response_schema(data)
        self.assertIn(
            "Data length mismatch for variable temperature_2m_mean",
            str(context.exception),
        )
