import requests
import pandas as pd
import matplotlib.pyplot as plt
from itertools import cycle

# Base URL for accessing the climate data API
API_URL = "https://climate-api.open-meteo.com/v1/climate?"

# Dictionary to store geographic coordinates for specific cities
COORDINATES = {
    "Madrid": {"latitude": 40.416775, "longitude": -3.703790},
    "London": {"latitude": 51.507351, "longitude": -0.127758},
    "Rio": {"latitude": -22.906847, "longitude": -43.172896},
}

# Define the climate metrics to fetch
VARIABLES = "temperature_2m_mean,precipitation_sum,soil_moisture_0_to_10cm_mean"  # noqa
MODELS = "CMCC_CM2_VHR4,FGOALS_f3_H,HiRAM_SIT_HR,MRI_AGCM3_2_S,EC_Earth3P_HR,MPI_ESM1_2_XR,NICAM16_8S"  # noqa
VARIABLES_MODELS = [
    f"{metric}_{model}"
    for metric in VARIABLES.split(",")
    for model in MODELS.split(",")
]


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

    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        data = response.json()
        try:
            validate_response_schema(data)
            return data["daily"]
        except Exception as e:
            print(f"Error validating response schema: {e}")
            return None

    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print("Too many requests. Please wait a bit before trying again.")
        else:
            print(f"HTTP Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def validate_response_schema(data):
    if "daily" not in data:
        raise Exception("Daily data not found in response.")

    base_metrics = [metric.split("_")[0] for metric in VARIABLES.split(",")]
    daily_keys = data["daily"].keys()

    for base_metric in base_metrics:
        if not any(key.startswith(base_metric) for key in daily_keys):
            raise Exception(f"Metric {base_metric} not found in response.")

    if "time" not in data["daily"]:
        raise Exception("Time data not found in response.")

    if len(data["daily"]["time"]) == 0:
        raise Exception("No time data found in response.")


def process_data(data):
    """Process the climate data to compute average and dispersion."""
    if not data:
        print("No data received.")
        return None
    try:
        timestamps = data.pop("time")
        metrics_dataframes = {}

        for metric in VARIABLES.split(","):
            metrics_dataframes[metric] = pd.DataFrame()

        for index, timestamp in enumerate(timestamps):
            variable_datapoints = {}
            for metric in VARIABLES.split(","):
                variable_datapoints[metric] = []
                for key, values in data.items():
                    if key.startswith(metric):
                        value = values[index]
                        variable_datapoints[metric].append(
                            value if value is not None else 0
                        )

            for metric, datapoints in variable_datapoints.items():
                avg = round(sum(datapoints) / len(datapoints), 4)
                std_deviation = round(
                    (sum((x - avg) ** 2 for x in datapoints) / len(datapoints)) ** 0.5,
                    4,
                )
                new_row = pd.DataFrame(
                    [
                        {
                            "timestamp": timestamp,
                            "mean": avg,
                            "std_deviation": std_deviation,
                        }
                    ],
                    index=[timestamp],
                )
                metrics_dataframes[metric] = pd.concat(
                    [metrics_dataframes[metric], new_row]
                )

        for metric, df in metrics_dataframes.items():
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)

        return metrics_dataframes

    except Exception as e:
        print(f"Error creating DataFrame or computing statistics: {e}")
        return None


def plot_climate_trends(processed_data, city):
    """Plot the processed climate data for a specific city,
    showing mean and std deviation."""
    num_metrics = len(VARIABLES.split(","))
    fig, axs = plt.subplots(num_metrics, 1, figsize=(20, num_metrics * 4), sharex=True)
    axs = axs if num_metrics > 1 else [axs]

    color_cycle = cycle(
        [
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
    )

    lines, labels = [], []
    for index, metric in enumerate(VARIABLES.split(",")):
        for key, df in processed_data.items():
            if key.startswith(metric):
                color = next(color_cycle)
                (line_mean,) = axs[index].plot(
                    df.index, df["mean"], label=f"{key} (mean)", color=color
                )
                fill_std_deviation = axs[index].fill_between(
                    df.index,
                    df["mean"] - df["std_deviation"],
                    df["mean"] + df["std_deviation"],
                    color=color,
                    alpha=0.1,
                    label=f"{metric} (std deviation)",
                )
                axs[index].set_ylabel(f"{metric} units")

                lines.extend([line_mean, fill_std_deviation])
                labels.extend([f"{key} (mean)", f"{key} (std deviation)"])

    plt.setp(axs[-1].xaxis.get_majorticklabels(), rotation=45)
    plt.xlabel("Date", loc="left")
    fig.suptitle(f"Climate Trends in {city}", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.legend(lines, labels, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.01))
    plt.savefig(f"src/module_1/images/climate_trends_{city}.png")


def main():
    for city in COORDINATES:
        try:
            data = get_data_meteo_api(city)
            if data:
                processed_data = process_data(data)
                if processed_data is not None:
                    plot_climate_trends(processed_data, city)
                else:
                    print(f"Data processing failed for {city}.")
            else:
                print(f"No data available to process for {city}.")
        except Exception as e:
            print(f"An error occurred while processing data for {city}: {e}")


if __name__ == "__main__":
    main()
