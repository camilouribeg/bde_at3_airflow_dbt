import os
import logging
import pandas as pd
import shutil
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

#########################################################
#
#   DAG Settings
#
#########################################################

dag_default_args = {
    "owner": "BDE_AT3",
    "start_date": datetime.now() - timedelta(days=1),
    "email": [],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "depends_on_past": False,
    "wait_for_downstream": False,
}

dag = DAG(
    dag_id="part1_raw_load",
    default_args=dag_default_args,
    schedule_interval=None,
    catchup=True,
    max_active_runs=1,
    concurrency=5,
)

#########################################################
#
#   Load Environment Variables
#
#########################################################
AIRFLOW_DATA = "/home/airflow/gcs/data"
DIMENSIONS = AIRFLOW_DATA + "/dimensions/"
FACTS = AIRFLOW_DATA + "/facts/"

#########################################################
#
#   Custom Logics for Operator
#
#########################################################


def import_load_dim_g01_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    g01_file_path = DIMENSIONS + "g01.csv"
    if not os.path.exists(g01_file_path):
        logging.info("No g01.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(g01_file_path, encoding="utf-8-sig")

    if len(df) > 0:
        col_names = ["LGA_CODE_2016", "Tot_P_M", "Tot_P_F"]
        values = df[col_names].to_dict("split")["data"]
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_census_g01(lga_code_2016, tot_p_m, tot_p_f)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, "archive")
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(g01_file_path, os.path.join(archive_folder, "g01.csv"))
    return None


def import_load_dim_g02_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    g02_file_path = DIMENSIONS + "g02.csv"
    if not os.path.exists(g02_file_path):
        logging.info("No g02.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(g02_file_path, encoding="utf-8-sig")

    if len(df) > 0:
        col_names = [
            "LGA_CODE_2016",
            "Median_age_persons",
            "Median_mortgage_repay_monthly",
            "Median_tot_hhd_inc_weekly",
        ]
        values = df[col_names].to_dict("split")["data"]
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_census_g02(lga_code_2016, median_age_persons, median_mortgage_repay_monthly, median_tot_hhd_inc_weekly)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, "archive")
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(g02_file_path, os.path.join(archive_folder, "g02.csv"))
    return None


def import_load_dim_lga_mapping_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    lga_mapping_file_path = DIMENSIONS + "lga_mapping.csv"
    if not os.path.exists(lga_mapping_file_path):
        logging.info("No lga_mapping.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(lga_mapping_file_path, encoding="utf-8-sig")

    if len(df) > 0:
        col_names = ["LGA_NAME", "SUBURB_NAME"]
        values = df[col_names].to_dict("split")["data"]
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_lga_mapping(lga_name, suburb_name)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, "archive")
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(
            lga_mapping_file_path, os.path.join(archive_folder, "lga_mapping.csv")
        )
    return None


def import_load_facts_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Get all files with '.csv' extension in the FACTS directory
    filelist = [k for k in os.listdir(FACTS) if ".csv" in k]

    # Check if there are any files to process
    if len(filelist) == 0:
        logging.info("No CSV files found in the FACTS directory.")
        return None  # Exit gracefully if no files are found

    # Generate dataframe by combining all files
    df = pd.concat(
        [
            pd.read_csv(os.path.join(FACTS, fname), encoding="utf-8-sig")
            for fname in filelist
        ],
        ignore_index=True,
    )

    if len(df) > 0:
        col_names = [
            "LISTING_ID",
            "LISTING_NEIGHBOURHOOD",
            "HOST_ID",
            "HOST_NEIGHBOURHOOD",
            "PROPERTY_TYPE",
            "ROOM_TYPE",
            "ACCOMMODATES",
            "HAS_AVAILABILITY",
            "AVAILABILITY_30",
            "PRICE",
            "SCRAPED_DATE",
        ]
        values = df[col_names].to_dict("split")["data"]
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_airbnb_listings(listing_id, listing_neighbourhood, host_id, host_neighbourhood, property_type, room_type, accommodates, has_availability, availability_30, price, scraped_date)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move processed files to the archive folder
        archive_folder = os.path.join(FACTS, "archive")
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)

        for fname in filelist:
            shutil.move(os.path.join(FACTS, fname), os.path.join(archive_folder, fname))
    return None


#########################################################
#
#   DAG Operator Setup
#
#########################################################

import_load_dim_g01_task = PythonOperator(
    task_id="import_load_dim_g01_id",
    python_callable=import_load_dim_g01_func,
    provide_context=True,
    dag=dag,
)

import_load_dim_g02_task = PythonOperator(
    task_id="import_load_dim_g02_id",
    python_callable=import_load_dim_g02_func,
    provide_context=True,
    dag=dag,
)

import_load_dim_lga_mapping_task = PythonOperator(
    task_id="import_load_dim_lga_mapping_id",
    python_callable=import_load_dim_lga_mapping_func,
    provide_context=True,
    dag=dag,
)

import_load_facts_task = PythonOperator(
    task_id="import_load_facts_id",
    python_callable=import_load_facts_func,
    provide_context=True,
    dag=dag,
)

# Task Dependencies
[
    import_load_dim_g01_task,
    import_load_dim_g02_task,
    import_load_dim_lga_mapping_task,
] >> import_load_facts_task
