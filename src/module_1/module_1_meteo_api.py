# Import the required libraries
import requests
import pandas as pd
import matplotlib.pyplot as plt
from itertools import cycle

# Base URL for accessing the climate data API
API_URL = "https://climate-api.open-meteo.com/v1/climate?"
# API_URL = "http://127.0.0.1:5000/api/climate?"

# Dictionary to store geographic coordinates for specific cities
COORDINATES = {
    "Madrid": {"latitude": 40.416775, "longitude": -3.703790},
    "London": {"latitude": 51.507351, "longitude": -0.127758},
    "Rio": {"latitude": -22.906847, "longitude": -43.172896},
}

# Define the variables to fetch
VARIABLES = "temperature_2m_mean,precipitation_sum,soil_moisture_0_to_10cm_mean"  # noqa
MODELS = "CMCC_CM2_VHR4,FGOALS_f3_H,HiRAM_SIT_HR,MRI_AGCM3_2_S,EC_Earth3P_HR,MPI_ESM1_2_XR,NICAM16_8S"  # noqa
VARIABLES_MODELS = [
    f"{variable}_{model}"
    for variable in VARIABLES.split(",")
    for model in MODELS.split(",")
]  # noqa


def get_data_meteo_api(city, start_year="2021-01-01", end_year="2022-12-31"):
    """Fetch climate data for a specific city within a given timeframe."""
    # Parameters for the API request
    params = {
        "latitude": COORDINATES[city]["latitude"],
        "longitude": COORDINATES[city]["longitude"],
        "start_date": start_year,
        "end_date": end_year,
        "models": MODELS,
        "daily": VARIABLES,
    }

    try:
        # Send the HTTP GET request to the API with the specified parameters
        response = requests.get(API_URL, params=params)
        # Raise an exception for response errors
        response.raise_for_status()

        data = response.json()
        try:
            validate_response_schema(data)
            return data["daily"]
        except Exception as e:
            print(f"Error validating response schema: {e}")
            return None

    except requests.exceptions.HTTPError as e:
        # Handle exceptions for HTTP errors like rate limits
        if response.status_code == 429:
            print("Too many requests. Please wait a bit before trying again.")
        else:
            print(f"HTTP Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        # Handle other request-related errors
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        # Handle JSON decoding errors
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        # Handle all other exceptions
        print(f"An unexpected error occurred: {e}")
        return None


def validate_response_schema(data):
    if "daily" not in data:
        raise Exception("Daily data not found in response.")

    for variable in VARIABLES_MODELS:
        if variable not in data["daily"]:
            raise Exception(f"Variable {variable} not found in response.")

    if "time" not in data["daily"]:
        raise Exception("Time data not found in response.")

    if len(data["daily"]["time"]) == 0:
        raise Exception("No time data found in response.")

    for variable in VARIABLES_MODELS:
        if len(data["daily"][variable]) != len(data["daily"]["time"]):
            raise Exception(f"Data length mismatch for variable {variable}.")


def process_data(data):
    """Process the data to compute average and dispersion."""
    # Check if data is empty
    if not data:
        print("No data received.")
        return None
    try:
        timestamps = data.pop("time")
        per_variable_dfs = {}

        for variable in VARIABLES.split(","):
            per_variable_dfs[variable] = pd.DataFrame()

        for index, timestamp in enumerate(timestamps):
            v_datapoints = {}
            for variable in VARIABLES.split(","):
                v_datapoints[variable] = []
                for key, values in data.items():
                    if key.startswith(variable):
                        value = values[index]
                        if (
                            value is not None
                        ):  # Check if the value is not None before appending
                            v_datapoints[variable].append(value)
                        else:
                            v_datapoints[variable].append(0)

            for variable in v_datapoints:
                if v_datapoints[
                    variable
                ]:  # Check if there are any data points to calculate avg and std
                    avg = sum(v_datapoints[variable]) / len(v_datapoints[variable])
                    std = (
                        sum([(x - avg) ** 2 for x in v_datapoints[variable]])
                        / len(v_datapoints[variable])
                    ) ** 0.5  # Standard deviation
                    new_row = pd.DataFrame(
                        [{"timestamp": timestamp, "mean": avg, "std": std}]
                    )
                    per_variable_dfs[variable] = pd.concat(
                        [per_variable_dfs[variable], new_row], ignore_index=True
                    )

        return per_variable_dfs

    except Exception as e:
        # Handle exceptions during data processing
        print(f"Error creating DataFrame or computing statistics: {e}")
        return None


def plot_data(data, city):
    """Plot the processed climate data for a specific city,
    showing mean and std."""

    num_variables = len(VARIABLES.split(","))
    fig, axs = plt.subplots(
        num_variables, 1, figsize=(20, num_variables * 4), sharex=True
    )

    if num_variables == 1:
        axs = [axs]

    # Define a list of colors to cycle through
    colors = [
        "blue",
        "green",
        "purple",
        "orange",
        "red",
        "cyan",
        "magenta",
        "yellow",
        "black",
    ]
    color_cycle = cycle(colors)

    lines = []
    labels = []

    for index, variable in enumerate(VARIABLES.split(",")):
        for key, df in data.items():
            if key.startswith(variable):
                color = next(color_cycle)
                (line_mean,) = axs[index].plot(
                    df.index, df["mean"], label=f"{key} (mean)", color=color
                )

                fill_std = axs[index].fill_between(
                    df.index,
                    df["mean"] - df["std"],
                    df["mean"] + df["std"],
                    color=color,
                    alpha=0.1,
                    label=f"{variable} (std deviation)",
                )
                axs[index].set_ylabel(f"{variable} units")

                # Add the line and fill objects to the legend list
                lines.append(line_mean)
                lines.append(fill_std)

                labels.append(f"{key} (mean)")
                labels.append(f"{key} (std deviation)")

    plt.setp(axs[-1].xaxis.get_majorticklabels(), rotation=45)
    plt.xlabel("Date", loc="left")
    fig.suptitle(f"Climate Trends in {city}", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Create a unified legend for all subplots at the bottom of the figure
    fig.legend(lines, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.01))

    plt.savefig(f"climate_trends_{city}.png")


def main():
    for city in COORDINATES:
        try:
            data = get_data_meteo_api(city)
            if data:
                processed_data = process_data(data)
                if processed_data is not None:
                    plot_data(processed_data, city)
                else:
                    print(f"Data processing failed for {city}.")
            else:
                print(f"No data available to process for {city}.")
        except Exception as e:
            print(f"An error occurred while processing data for {city}: {e}")
            print(e)


if __name__ == "__main__":
    main()
