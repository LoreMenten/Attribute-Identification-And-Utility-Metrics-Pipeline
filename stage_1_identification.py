import pandas as pd
import numpy as np
from collections import Counter


# Function to filter columns for NA
def filter_columns_NA(df):
    df = df.fillna("missing")
    n_rows = len(df.index)
    n_cols = len(df.columns)
    columns_to_drop = []
    for col in range(n_cols):
        col_name = df.columns[col]
        col_values = df.iloc[:, col]
        na_count = sum(col_values == "missing")
        na_percentage = na_count / n_rows * 100
        if "missing" in df.values and na_percentage > 85:
            columns_to_drop.append(col_name)
            print("Columns excluded because of missing values:")
            print(f"\t{col_name}: {na_percentage}")
    df.drop(columns_to_drop, axis=1, inplace=True)
    return df


# Function to calculate g-distinct
def compute_g_distinct(df):
    n_cols = len(df.columns)
    n_rows = len(df)
    g_distinct_dict = {}

    for col in range(n_cols):
        cols_values_to_g = {}
        cols_values = df.iloc[:, col]
        cols_values_to_amounts = Counter(cols_values)
        for row in range(n_rows):
            value = df.iloc[row, col]
            value_count = cols_values_to_amounts[value]
            if value not in cols_values_to_g:
                cols_values_to_g[value] = 1 / value_count
        g_distinct_dict[df.columns[col]] = list(cols_values_to_g.values())

    return g_distinct_dict


# Function to calculate re-identification risk rate
def calculate_reidentification_risk(g_distinct_values):
    reidentification_risk_rates_dict = {}

    for key in g_distinct_values:
        g_distinct_attr = g_distinct_values[key]
        length = len(g_distinct_attr)
        reidentification_risk_rates_dict[key] = round(
            (np.sum(g_distinct_attr) / length) * 100, 2
        )
    return reidentification_risk_rates_dict


# Function to classify columns according to thesholds
def classify_columns(risk_rates, beta, alpha):
    QIDs = {}
    SAs = {}
    NSs = {}

    for key in risk_rates:
        risk_rate = risk_rates[key]
        if alpha >= risk_rate >= beta:
            QIDs[key] = risk_rate
        elif risk_rate > alpha:
            SAs[key] = risk_rate
        else:
            NSs[key] = risk_rate

    return QIDs, SAs, NSs


# Execute code
df = pd.read_csv(input("Enter the path of your dataframe: "))
print()

column_to_drop_count = 1
column_to_drop = input(
    f"Give the column name of direct identifier {column_to_drop_count} (press Enter to stop): "
)
while len(column_to_drop) > 0:
    df = df.drop(column_to_drop, axis=1)
    column_to_drop_count = column_to_drop_count + 1
    column_to_drop = input(
        f"Give the column name of direct identifier {column_to_drop_count} (press Enter to stop): "
    )
print()

df = filter_columns_NA(df)
print()

g_distinct_values = compute_g_distinct(df)

risk_rates = calculate_reidentification_risk(g_distinct_values)

print("Re-identification risk rates:")
for key in sorted(risk_rates, key=risk_rates.get, reverse=True):
    print(f"\t{key}: {risk_rates[key]}")
print()

alpha_threshold = float(input("Enter the α threshold (as a float): "))
print()
beta_threshold = float(input("Enter the β threshold (as a float): "))
print()

QIDs, SAs, NSs = classify_columns(risk_rates, beta_threshold, alpha_threshold)

print("Sensitive attributes:")
for key in sorted(SAs, key=SAs.get, reverse=True):
    print(f"\t{key}: {SAs[key]}")
print()
print("Quasi-identifiers:")
for key in sorted(QIDs, key=QIDs.get, reverse=True):
    print(f"\t{key}: {QIDs[key]}")
print()
print("Non-sensitive attributes:")
for key in sorted(NSs, key=NSs.get, reverse=True):
    print(f"\t{key}: {NSs[key]}")
print()

print("Advice:")
print("\tDe-identify the columns according to their re-identification risk rates.")
print(
    "\tStart with the column with the highest risk rate and end with the column with the lowest risk rate."
)
print("\tAfterwards, proceed to the QID dimension stage.")
print()
