from google.cloud import bigquery
import time 

def prepare_data(manufacturing_data):  
    client = bigquery.Client(
        project='airflow-408713',
        location='europe-west1'
    )
   
    # Delete existing table
    client.query("DROP TABLE IF EXISTS airflow-408713.manufacturing_data.manufacturing;").result()

    time.sleep(10)
    # Create new table
    client.query("""
    CREATE TABLE airflow-408713.manufacturing_data.manufacturing (
    job_id BIGINT NOT NULL,
    priority BIGINT NOT NULL,
    smd_0 INT64 NOT NULL,
    smd_1 INT64 NOT NULL,
    smd_2 INT64 NOT NULL,
    smd_3 INT64 NOT NULL,
    smd_4 INT64 NOT NULL, 
    processing_time_s1 BIGINT NOT NULL,
    aoi_0 INT64 NOT NULL,
    aoi_1 INT64 NOT NULL,
    aoi_2 INT64 NOT NULL,
    aoi_3 INT64 NOT NULL,
    aoi_4 INT64 NOT NULL,
    processing_time_s2 BIGINT NOT NULL,
    ss_0 INT64 NOT NULL,
    ss_1 INT64 NOT NULL,
    ss_2 INT64 NOT NULL,
    ss_3 INT64 NOT NULL,
    ss_4 INT64 NOT NULL,
    processing_time_s3 BIGINT NOT NULL,
    cc_0 INT64 NOT NULL,
    cc_1 INT64 NOT NULL,
    processing_time_s4 INT64 NOT NULL,
    overall_processing_time INT64 NOT NULL,
    overall_waiting_time INT64 NOT NULL,
    tardiness INT64 NOT NULL,
    breaks INT64 NOT NULL
);
    """)
    time.sleep(10)


    # Insert Data from CSV 
    rows_to_insert = []
    for row in manufacturing_data:
        first_stage, second_stage, third_stage, fourth_stage = row[3], row[7], row[11], row[15] 
        # First Stage to binary attributes
        smd_0_value = 1 if first_stage == "SMD_0" else 0
        smd_1_value = 1 if first_stage == "SMD_1" else 0
        smd_2_value = 1 if first_stage == "SMD_2" else 0
        smd_3_value = 1 if first_stage == "SMD_3" else 0
        smd_4_value = 1 if first_stage == "SMD_4" else 0

        # Second stage to binary attributes
        aoi_0_value = 1 if second_stage == "AOI_0" else 0
        aoi_1_value = 1 if second_stage == "AOI_1" else 0
        aoi_2_value = 1 if second_stage == "AOI_2" else 0
        aoi_3_value = 1 if second_stage == "AOI_3" else 0
        aoi_4_value = 1 if second_stage == "AOI_4" else 0

        # Third stage binary attributes
        ss_0_value =  1 if third_stage == "SS_0" else 0
        ss_1_value =  1 if third_stage == "SS_1" else 0
        ss_2_value =  1 if third_stage == "SS_2" else 0
        ss_3_value =  1 if third_stage == "SS_3" else 0    
        ss_4_value =  1 if third_stage == "SS_4" else 0

        # Fourth stage binary attributes
        cc_0_value = 1 if fourth_stage == "CC_0" else 0
        cc_1_value = 1 if fourth_stage == "CC_1" else 0

        row_to_append = {
            "job_id": row[0],
            "priority": row[1],
            "smd_0": smd_0_value,
            "smd_1": smd_1_value, 
            "smd_2": smd_2_value,
            "smd_3": smd_3_value,
            "smd_4": smd_4_value,
            "processing_time_s1": row[6],
            "aoi_0": aoi_0_value,
            "aoi_1": aoi_1_value,
            "aoi_2": aoi_2_value,
            "aoi_3": aoi_3_value,
            "aoi_4": aoi_4_value,
            "processing_time_s2": row[10],
            "ss_0": ss_0_value,
            "ss_1": ss_1_value,
            "ss_2": ss_2_value,
            "ss_3": ss_3_value,
            "ss_4": ss_4_value,
            "processing_time_s3": row[14],
            "cc_0": cc_0_value,
            "cc_1": cc_1_value, 
            "processing_time_s4": row[18],
            "overall_processing_time": row[19],
            "overall_waiting_time": row[20],
            "tardiness": row[21],
            "breaks": row[22]        
        }

        rows_to_insert.append(row_to_append)

    errors = client.insert_rows_json("airflow-408713.manufacturing_data.manufacturing", rows_to_insert)
        
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))
