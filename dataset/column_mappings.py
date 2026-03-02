"""
HR Dataset Column Mappings
===========================
Lookup dictionaries for encoded numeric columns in the HR Employee Attrition dataset.
Use these mappings to decode numeric codes into human-readable labels.
"""

Education = {
    1: "Below College",
    2: "College",
    3: "Bachelor",
    4: "Master",
    5: "Doctor",
}

EnvironmentSatisfaction = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Very High",
}

JobInvolvement = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Very High",
}

JobSatisfaction = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Very High",
}

PerformanceRating = {
    1: "Low",
    2: "Good",
    3: "Excellent",
    4: "Outstanding",
}

RelationshipSatisfaction = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Very High",
}

WorkLifeBalance = {
    1: "Bad",
    2: "Good",
    3: "Better",
    4: "Best",
}

# Combined mapping for convenient access
ALL_MAPPINGS = {
    "Education": Education,
    "EnvironmentSatisfaction": EnvironmentSatisfaction,
    "JobInvolvement": JobInvolvement,
    "JobSatisfaction": JobSatisfaction,
    "PerformanceRating": PerformanceRating,
    "RelationshipSatisfaction": RelationshipSatisfaction,
    "WorkLifeBalance": WorkLifeBalance,
}


def decode_column(df, column_name):
    """
    Replace numeric codes in a DataFrame column with their string labels.

    Parameters
    ----------
    df : pandas.DataFrame
    column_name : str  — must be one of the keys in ALL_MAPPINGS

    Returns
    -------
    pandas.Series with decoded values.
    """
    mapping = ALL_MAPPINGS.get(column_name)
    if mapping is None:
        raise ValueError(f"No mapping found for column '{column_name}'. "
                         f"Available: {list(ALL_MAPPINGS.keys())}")
    return df[column_name].map(mapping)


def decode_all(df):
    """
    Return a copy of *df* with all mapped columns replaced by their string labels.
    """
    df = df.copy()
    for col in ALL_MAPPINGS:
        if col in df.columns:
            df[col] = df[col].map(ALL_MAPPINGS[col])
    return df
