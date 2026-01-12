from kfp.dsl import component, Dataset, Output, Input


@component(
    base_image="python:3.10",
    packages_to_install=["pandas"],
)
def prepare_data_op(
    raw_data: Input[Dataset],
    prepared_data: Output[Dataset],
):
    import pandas as pd
    import os

    # -------------------------------
    # 1. Load raw data
    # -------------------------------
    raw_data_path = os.path.join(raw_data.path, "raw_data.csv")

    # Raw file has no header (column positions are fixed)
    df = pd.read_csv(raw_data_path)

    prepared_rows = []

    # -------------------------------
    # 2. Row-wise feature engineering
    # -------------------------------
    for _, row in df.iterrows():
        first_stage  = row.iloc[3]
        second_stage = row.iloc[7]
        third_stage  = row.iloc[11]
        fourth_stage = row.iloc[15]

        prepared_rows.append({
            # Identifiers / metadata
            "job_id": row.iloc[0],
            "priority": row.iloc[1],

            # -------- First stage (SMD) --------
            "smd_0": int(first_stage == "SMD_0"),
            "smd_1": int(first_stage == "SMD_1"),
            "smd_2": int(first_stage == "SMD_2"),
            "smd_3": int(first_stage == "SMD_3"),
            "smd_4": int(first_stage == "SMD_4"),
            "processing_time_s1": row.iloc[6],

            # -------- Second stage (AOI) --------
            "aoi_0": int(second_stage == "AOI_0"),
            "aoi_1": int(second_stage == "AOI_1"),
            "aoi_2": int(second_stage == "AOI_2"),
            "aoi_3": int(second_stage == "AOI_3"),
            "aoi_4": int(second_stage == "AOI_4"),
            "processing_time_s2": row.iloc[10],

            # -------- Third stage (SS) --------
            "ss_0": int(third_stage == "SS_0"),
            "ss_1": int(third_stage == "SS_1"),
            "ss_2": int(third_stage == "SS_2"),
            "ss_3": int(third_stage == "SS_3"),
            "ss_4": int(third_stage == "SS_4"),
            "processing_time_s3": row.iloc[14],

            # -------- Fourth stage (CC) --------
            "cc_0": int(fourth_stage == "CC_0"),
            "cc_1": int(fourth_stage == "CC_1"),
            "processing_time_s4": row.iloc[18],

            # -------- Global KPIs --------
            "overall_processing_time": row.iloc[19],
            "overall_waiting_time": row.iloc[20],
            "tardiness": row.iloc[21],

            # -------- Target --------
            "breaks": row.iloc[22],
        })

    # -------------------------------
    # 3. Save prepared dataset
    # -------------------------------
    prepared_df = pd.DataFrame(prepared_rows)

    os.makedirs(prepared_data.path, exist_ok=True)
    output_path = os.path.join(prepared_data.path, "prepared_data.csv")
    prepared_df.to_csv(output_path, index=False)

    print("Prepared data written to:", output_path)
