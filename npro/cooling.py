import pandas as pd

NORMALIZED_HEATING_REFERENCE_TEMPERATURE = -12
NORMALIZED_COOLING_REFERENCE_TEMPERATURE = 38


def extract_airtemp_from_csv(file_path):
    """
    Extracts air temperature from a CSV file into a pandas.Series.
    Index contains datetimes and values contain airtemp.
    """
    df = pd.read_csv(file_path)
    # The CSV has month, day, hour. We'll assume a dummy year (e.g., 2021) for creating datetimes
    # or just use the columns if they are sufficient.
    # From inspection: "month","day","hour","doy",...
    # Hour seems to be 0-23.
    # We will create a datetime index.
    df["year"] = 2021  # Dummy year
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    series = df.set_index("datetime")["air_temperature_mean"]
    return series


def calculate_cdd(airtemp_series, base_temp, limit_temp, case="heating"):
    """
    Calculates Cooling Degree Days (CDD) from a pandas.Series.
    CDD = sum(max(0, T_avg - T_base)) for each day.
    """
    if isinstance(airtemp_series, dict):
        airtemp_series = pd.Series(
            airtemp_series["airTemp"],
            index=pd.date_range(
                start="2026-01-01 00:00:00", freq="h", periods=len(airtemp_series["airTemp"])
            ),
        )

    # Resample to daily mean
    daily_avg_temps = airtemp_series.resample("D").mean()

    total_cdd = 0.0
    daily_results = {}

    for date, avg_temp in daily_avg_temps.items():
        if case == "heating":
            if avg_temp < limit_temp:
                cdd_day = max(0, base_temp - avg_temp)
            else:
                cdd_day = 0
        else:
            if avg_temp > limit_temp:
                cdd_day = max(0, avg_temp - base_temp)
            else:
                cdd_day = 0
        total_cdd += cdd_day

        day_tuple = (str(date.month), str(date.day))
        daily_results[day_tuple] = {"avg_temp": avg_temp, "cdd": cdd_day}

    return total_cdd


def calculate_heat_demand(
    cdd, max_heat_power, base_temp, norm_temp=NORMALIZED_HEATING_REFERENCE_TEMPERATURE
):
    delta_t = base_temp - norm_temp
    return cdd * max_heat_power / 1000 * 24 / delta_t


def calculate_cool_demand(
    cdd, max_cool_power, base_temp, norm_temp=NORMALIZED_COOLING_REFERENCE_TEMPERATURE
):
    delta_t = norm_temp - base_temp
    return cdd * max_cool_power / 1000 * 24 / delta_t


if __name__ == "__main__":
    file_path = "weather/npro_ref.csv"
    airtemp_series = extract_airtemp_from_csv(file_path)

    # Heating
    temp_limit = 15
    temp_innen = 70
    hdd = calculate_cdd(
        airtemp_series, base_temp=temp_innen, limit_temp=temp_limit
    )
    print(f"Total HGT: {hdd:.2f}")
    heat_demand = calculate_heat_demand(
        hdd, max_heat_power=79.5, base_temp=temp_innen
    )
    print(f"Total heat demand: {heat_demand:.2f}")

    # Cooling
    base_temp = 12
    cdd = calculate_cdd(
        airtemp_series, base_temp=base_temp, limit_temp=18, case="cooling"
    )
    print(f"Total CDD: {cdd:.2f}")
    heat_demand = calculate_cool_demand(
        cdd, max_cool_power=40, base_temp=base_temp
    )
    print(f"Total cool demand: {heat_demand:.2f}")
