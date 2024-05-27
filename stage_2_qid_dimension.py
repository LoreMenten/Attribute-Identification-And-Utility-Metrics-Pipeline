import pandas as pd
import numpy as np
from collections import Counter
from pycanon.anonymity.utils import aux_anonymity
from pycanon.anonymity.utils import aux_functions


# Function to compute k-anonymity
def compute_k_anonymity(df, quasi_identifiers):
    grouped_df = df.groupby(quasi_identifiers)

    group_sizes = []
    for _, group in grouped_df:
        group_size = len(group)
        group_sizes.append(group_size)

    min_k_anonymity = min(group_sizes)
    return min_k_anonymity


# Function to compute l-diversity
def compute_l_diversity(df, quasi_identifiers, sensitive_attribute):
    grouped_df = df.groupby(quasi_identifiers)

    l_diversities = []
    for _, group in grouped_df:
        l_diversity = len(group[sensitive_attribute].unique())
        l_diversities.append(l_diversity)

    min_l_diversity = min(l_diversities)
    return min_l_diversity


# Function to compute t-closeness
def compute_t_closeness(df, quasi_ident, sens_att, gen=True):
    quasi_ident = np.array(quasi_ident)
    sens_att = np.array(sens_att)
    aux_functions.check_qi(df, quasi_ident)
    aux_functions.check_sa(df, sens_att)
    t_sens_att = []
    if gen:
        for sens_att_value in sens_att:
            if pd.api.types.is_numeric_dtype(df[sens_att_value]):
                t_sens_att.append(
                    aux_anonymity.aux_t_closeness_num(df, quasi_ident, sens_att_value)
                )
            elif pd.api.types.is_string_dtype(df[sens_att_value]):
                t_sens_att.append(
                    aux_anonymity.aux_t_closeness_str(df, quasi_ident, sens_att_value)
                )
            else:
                raise ValueError("Error, invalid sens_att value type")
    else:
        for i, sens_att_value in enumerate(sens_att):
            if pd.api.types.is_numeric_dtype(df[sens_att_value]):
                tmp_qi = np.concatenate([quasi_ident, np.delete(sens_att, i)])
                t_sens_att.append(
                    aux_anonymity.aux_t_closeness_num(df, tmp_qi, sens_att_value)
                )
            elif pd.api.types.is_string_dtype(df[sens_att_value]):
                tmp_qi = np.concatenate([quasi_ident, np.delete(sens_att, i)])
                t_sens_att.append(
                    aux_anonymity.aux_t_closeness_str(df, tmp_qi, sens_att_value)
                )
            else:
                raise ValueError("Error, invalid sens_att value type")
    return max(t_sens_att)


# Function to compute privacy gain
def compute_privacy_gain(k_anonymity_after, k_anonymity_original):
    privacy_gain = k_anonymity_after - k_anonymity_original
    return privacy_gain


# Function to compute non-uniform entropy
def compute_non_uniform_entropy(df_original, df_after, selected_quasi_identifiers):
    non_uniform_entropy = 0

    for column in selected_quasi_identifiers:
        if column in df_original.columns and column in df_after.columns:
            original_values = df_original[column]
            after_values = df_after[column]
            original_values_to_amount = Counter(original_values)
            after_values_to_amount = Counter(after_values)
            for index in range(len(original_values)):
                original_value = original_values[index]
                after_value = after_values[index]
                original_amount = original_values_to_amount[original_value]
                after_amount = after_values_to_amount[after_value]
                if original_amount > 0 and after_amount > 0:
                    ratio = original_amount / after_amount
                    non_uniform_entropy -= np.log(ratio)

    return non_uniform_entropy


# Function to turn non-uniform entropy into a percentage
def value_to_percentage(nue, min_nue, max_nue):
    percentage = ((nue - min_nue) / (max_nue - min_nue)) * 100
    return round(percentage, 2)


# Function to filter k-anonymity
def filter_k_anonymity(qid_dimension):
    return qid_dimension["k_anonymity_after"] >= 2


# Function to calculate the optimal QID dimension
def find_optimal_qid_dimension(qid_dimension_list):
    filtered_list = list(filter(filter_k_anonymity, qid_dimension_list))
    max_record = filtered_list[0]

    for item in filtered_list:
        current_pg = item["pg"]
        current_nue = item["inverse_nue"]
        current_k = item["k_anonymity_after"]
        if (
            current_pg >= max_record["pg"]
            and current_nue >= max_record["inverse_nue"]
            and current_k >= 2
        ):
            current_difference = abs(current_pg - current_nue)
            min_difference = abs(max_record["pg"] - max_record["inverse_nue"])
            if current_difference < min_difference:
                max_record = item

    return max_record["qid_dimension"]


# Execute code
stop = False
df_original = pd.read_csv(
    input(
        "Enter the path of your original dataframe (SAs should be de-identified, DIDs and columns where missing values > 85 percent should be suppressed): "
    )
)
print()
df_final = pd.read_csv(
    input("Enter the path of your dataframe where all information is removed: ")
)
print()
quasi_identifiers = input("Enter all QIDs (as strings seperated by commas): ")
print()
sensitive_attributes = input(
    "Enter all sensitive attributes (as strings seperated by commas): "
)
print()
if "," in quasi_identifiers:
    quasi_identifiers = quasi_identifiers.split(",")
else:
    quasi_identifiers = [quasi_identifiers]
quasi_identifiers = list(
    map(
        lambda qid: qid.replace(" ", "").replace('"', ""),
        quasi_identifiers,
    )
)
if "," in sensitive_attributes:
    sensitive_attributes = sensitive_attributes.split(",")
else:
    sensitive_attributes = [sensitive_attributes]
sensitive_attributes = list(
    map(
        lambda sensitive_attribute: sensitive_attribute.replace(" ", "").replace(
            '"', ""
        ),
        sensitive_attributes,
    )
)

while not stop:
    de_identified_quasi_identifiers = input(
        "Enter the de-identified QIDs (as strings seperated by commas): "
    )
    print()
    df_after = pd.read_csv(input("Enter the path of your de-identified dataframe: "))
    print()
    print("De-identified QIDs:", de_identified_quasi_identifiers)
    print()
    if "," in de_identified_quasi_identifiers:
        de_identified_quasi_identifiers = de_identified_quasi_identifiers.split(",")
    else:
        de_identified_quasi_identifiers = [de_identified_quasi_identifiers]
    de_identified_quasi_identifiers = list(
        map(
            lambda qid: qid.replace(" ", "").replace('"', ""),
            de_identified_quasi_identifiers,
        )
    )

    k_anonymity_original = compute_k_anonymity(df_original, quasi_identifiers)
    print("\tK-anonymity original:\t\t", k_anonymity_original)
    print()
    k_anonymity_after = compute_k_anonymity(df_after, quasi_identifiers)
    print("\tK-anonymity after:\t\t", k_anonymity_after)
    print()
    t_closeness_original = compute_t_closeness(
        df_original, quasi_identifiers, sensitive_attributes
    )
    print("\tT-closeness original:\t\t", t_closeness_original)
    print()
    t_closeness_after = compute_t_closeness(
        df_after, quasi_identifiers, sensitive_attributes
    )
    print("\tT-closeness after:\t\t", t_closeness_after)
    print()
    for sensitive_attribute in sensitive_attributes:
        print("\t\tSensitive attributes:", sensitive_attribute)
        print()
        l_diversity_original = compute_l_diversity(
            df_original, quasi_identifiers, sensitive_attribute
        )
        print("\t\t\tL-diversity original:\t", l_diversity_original)
        print()
        l_diversity_after = compute_l_diversity(
            df_after, quasi_identifiers, sensitive_attribute
        )
        print("\t\t\tL-diversity after:\t", l_diversity_after)
        print()

    pg = compute_privacy_gain(k_anonymity_after, k_anonymity_original)
    print("\tPrivacy gain:\t\t\t", pg)
    print()
    nue = compute_non_uniform_entropy(
        df_original, df_after, de_identified_quasi_identifiers
    )
    max_nue = compute_non_uniform_entropy(df_original, df_final, quasi_identifiers)
    min_nue = compute_non_uniform_entropy(df_original, df_original, quasi_identifiers)
    nue_percentage = value_to_percentage(nue, min_nue, max_nue)
    inverse_nue_percentage = 100 - value_to_percentage(nue, min_nue, max_nue)
    qid_dimension_list = []
    print("\tNon-uniform entropy:\t\t", nue)
    print()
    print("\tNon-uniform entropy(%):\t\t", nue_percentage)
    print()
    print("\tInverse non-uniform entropy(%):\t", inverse_nue_percentage)
    print()
    qid_dimension_list.append(
        {
            "pg": pg,
            "inverse_nue": inverse_nue_percentage,
            "k_anonymity_after": k_anonymity_after,
            "qid_dimension": len(de_identified_quasi_identifiers),
        }
    )

    stop = len(quasi_identifiers) == len(de_identified_quasi_identifiers)
    if stop:
        print("All QIDS were processed")
        print()


# Find the optimal QID dimension
optimal_qidD_result = find_optimal_qid_dimension(qid_dimension_list)


print("Optimal QID Dimension:", optimal_qidD_result)
print()

print("Advice:")
print(f"\tYou should de-identify the first {optimal_qidD_result} QIDS.")
print()
