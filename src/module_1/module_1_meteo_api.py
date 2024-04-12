import requests
import pandas as pd
import matplotlib.pyplot as plt

# Path: climate_api.py
# API_URL = "https://climate-api.open-meteo.com/v1/climate?"
API_URL = "http://127.0.0.1:5000/api/climate?"


# Set the coordinates for the cities
COORDINATES = {
    "Madrid": {"latitude": 40.416775, "longitude": -3.703790},
    "London": {"latitude": 51.507351, "longitude": -0.127758},
    "Rio": {"latitude": -22.906847, "longitude": -43.172896},
}

# Define the variables to fetch
VARIABLES = "temperature_2m_mean,precipitation_sum,soil_moisture_0_to_10cm_mean"  # noqa
MODELS = "CMCC_CM2_VHR4,FGOALS_f3_H,HiRAM_SIT_HR,MRI_AGCM3_2_S,EC_Earth3P_HR,MPI_ESM1_2_XR,NICAM16_8S"  # noqa


def get_data_meteo_api(city, start_year="1950-01-01", end_year="2050-12-31"):
    """Fetch climate data for a specific city within a given timeframe."""
    params = {
        "latitude": COORDINATES[city]["latitude"],
        "longitude": COORDINATES[city]["longitude"],
        "start_date": start_year,
        "end_date": end_year,
        "models": MODELS,
        "daily": VARIABLES,
    }

    # TODO: Add rate limits and proper error handling --> Try/Except
    # TODO: Add schema validation for the response

    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "daily" in data:
            return data["daily"]
        else:
            print("Daily data not found in response.")
            return None
    elif response.status_code == 429:
        print("Too many requests. Please wait a bit before trying again.")
        return None
    else:
        print("Failed to fetch or parse data.")
        return None


def process_data(data):
    # TODO: Add unit tests
    """Process the data to compute average and dispersion."""
    if not data:
        print("No data received.")
        return None
    try:
        timestamps = data.pop("time")

        per_variable_dfs = {}
        for variable in data:
            df = pd.DataFrame(
                data[variable], index=timestamps, columns=[variable]
            )  # noqa
            df.index = pd.to_datetime(df.index)
            new_df = df.groupby(df.index.date)[variable].agg(["mean", "std"])
            new_df.columns = ["mean", "std"]
            new_df.index = pd.to_datetime(new_df.index)
            per_variable_dfs[variable] = new_df

        return per_variable_dfs

    except Exception as e:
        print(f"Error creating DataFrame or computing statistics: {e}")
        return None


def plot_data(data, city):
    """Plot the climate data for a specific city."""
    fig, axs = plt.subplots(len(data.keys()), figsize=(10, 6))

    for i, (variable, df) in enumerate(data.items()):
        axs[i].plot(df.index.date, df["mean"], label=f"{variable} (mean)")
        axs[i].fill_between(
            df.index,
            df["mean"] - df["std"],
            df["mean"] + df["std"],
            alpha=0.2,
            label=f"{variable} (std)",
        )
        axs[i].set_ylabel(variable)
        axs[i].legend()
        if i < len(data.keys()) - 1:
            plt.setp(axs[i].xaxis.get_majorticklabels(), visible=False)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"climate_trends_{city}.png")


def main():
    for city in COORDINATES:
        data = get_data_meteo_api(city)
        if data:
            processed_data = process_data(
                data,
            )
            if processed_data is not None:
                plot_data(processed_data, city)
            else:
                print(f"Data processing failed for {city}.")

        else:
            print(f"Failed to fetch data for {city}.")


if __name__ == "__main__":
    main()
