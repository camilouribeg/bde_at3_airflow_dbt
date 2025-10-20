import os
import logging
import requests
import pandas as pd
import shutil
from datetime import datetime, timedelta
from psycopg2.extras import execute_values
from airflow import AirflowException
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable

#########################################################
#
#   DAG Settings
#
#########################################################

dag_default_args = {
    "owner": "BDE_AIRBNB_DBT",
    "start_date": datetime.now() - timedelta(days=2),
    "email": [],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "depends_on_past": False,
    "wait_for_downstream": False,
}

dag = DAG(
    dag_id="airbnb_trigger_dbt",
    default_args=dag_default_args,
    schedule_interval=None,  # Manual trigger
    catchup=False,
    max_active_runs=1,
    concurrency=2,
    description="Monthly Airbnb Data Pipeline with dbt Cloud Integration",
)

#########################################################
#
#   Load Environment Variables
#
#########################################################
AIRFLOW_DATA = "/home/airflow/gcs/data"
AIRBNB_DATA = AIRFLOW_DATA + "/listings/"
CENSUS_DATA = AIRFLOW_DATA + "/census/"
DIMENSIONS_DATA = AIRFLOW_DATA + "/dimensions/"

#########################################################
#
#   Custom Functions for Data Loading
#
#########################################################


def load_airbnb_listings_func(**kwargs):
    """
    Load Airbnb listings data from CSV files into bronze layer
    """
    logging.info("Starting Airbnb listings data load...")

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the directory exists
    if not os.path.exists(AIRBNB_DATA):
        logging.warning(f"Airbnb data directory {AIRBNB_DATA} not found.")
        return None

    # Get all CSV files in the listings directory
    filelist = [f for f in os.listdir(AIRBNB_DATA) if f.endswith(".csv")]

    if len(filelist) == 0:
        logging.info("No CSV files found in the Airbnb listings directory.")
        return None

    logging.info(f"Found {len(filelist)} CSV files to process: {filelist}")

    # Process each file
    for filename in filelist:
        file_path = os.path.join(AIRBNB_DATA, filename)
        logging.info(f"Processing file: {filename}")

        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            logging.info(f"Loaded {len(df)} rows from {filename}")

            if len(df) > 0:
                # Define column mapping (adjust based on your actual CSV structure)
                # This assumes your CSV has the standard Airbnb columns
                col_names = list(df.columns)
                values = df[col_names].to_dict("split")["data"]

                # Insert into bronze table
                insert_sql = f"""
                    INSERT INTO bronze.raw_airbnb_listings({','.join(col_names)})
                    VALUES %s
                    ON CONFLICT DO NOTHING
                """

                result = execute_values(
                    conn_ps.cursor(), insert_sql, values, page_size=1000
                )
                conn_ps.commit()
                logging.info(f"Successfully loaded {len(df)} rows from {filename}")

                # Move processed file to archive
                archive_folder = os.path.join(AIRBNB_DATA, "archive")
                if not os.path.exists(archive_folder):
                    os.makedirs(archive_folder)
                shutil.move(file_path, os.path.join(archive_folder, filename))
                logging.info(f"Moved {filename} to archive")

        except Exception as e:
            logging.error(f"Error processing {filename}: {str(e)}")
            raise AirflowException(f"Failed to process {filename}: {str(e)}")

    logging.info("Airbnb listings data load completed successfully")
    return None


def load_census_data_func(**kwargs):
    """
    Load Census data (G01, G02) into bronze layer
    """
    logging.info("Starting Census data load...")

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Process G01 data
    g01_file = os.path.join(DIMENSIONS_DATA, "g01.csv")
    if os.path.exists(g01_file):
        logging.info("Loading G01 Census data...")
        try:
            df = pd.read_csv(g01_file)
            col_names = list(df.columns)
            values = df[col_names].to_dict("split")["data"]

            insert_sql = f"""
                INSERT INTO bronze.raw_census_g01({','.join(col_names)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """

            result = execute_values(
                conn_ps.cursor(), insert_sql, values, page_size=1000
            )
            conn_ps.commit()
            logging.info(f"Successfully loaded {len(df)} rows from G01")

            # Archive file
            archive_folder = os.path.join(DIMENSIONS_DATA, "archive")
            if not os.path.exists(archive_folder):
                os.makedirs(archive_folder)
            shutil.move(g01_file, os.path.join(archive_folder, "g01.csv"))

        except Exception as e:
            logging.error(f"Error loading G01 data: {str(e)}")
            raise AirflowException(f"Failed to load G01 data: {str(e)}")

    # Process G02 data
    g02_file = os.path.join(DIMENSIONS_DATA, "g02.csv")
    if os.path.exists(g02_file):
        logging.info("Loading G02 Census data...")
        try:
            df = pd.read_csv(g02_file)
            col_names = list(df.columns)
            values = df[col_names].to_dict("split")["data"]

            insert_sql = f"""
                INSERT INTO bronze.raw_census_g02({','.join(col_names)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """

            result = execute_values(
                conn_ps.cursor(), insert_sql, values, page_size=1000
            )
            conn_ps.commit()
            logging.info(f"Successfully loaded {len(df)} rows from G02")

            # Archive file
            archive_folder = os.path.join(DIMENSIONS_DATA, "archive")
            if not os.path.exists(archive_folder):
                os.makedirs(archive_folder)
            shutil.move(g02_file, os.path.join(archive_folder, "g02.csv"))

        except Exception as e:
            logging.error(f"Error loading G02 data: {str(e)}")
            raise AirflowException(f"Failed to load G02 data: {str(e)}")

    # Process LGA mapping data
    lga_mapping_file = os.path.join(DIMENSIONS_DATA, "lga_mapping.csv")
    if os.path.exists(lga_mapping_file):
        logging.info("Loading LGA mapping data...")
        try:
            df = pd.read_csv(lga_mapping_file)
            col_names = list(df.columns)
            values = df[col_names].to_dict("split")["data"]

            insert_sql = f"""
                INSERT INTO bronze.raw_lga_mapping({','.join(col_names)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """

            result = execute_values(
                conn_ps.cursor(), insert_sql, values, page_size=1000
            )
            conn_ps.commit()
            logging.info(f"Successfully loaded {len(df)} rows from LGA mapping")

            # Archive file
            archive_folder = os.path.join(DIMENSIONS_DATA, "archive")
            if not os.path.exists(archive_folder):
                os.makedirs(archive_folder)
            shutil.move(
                lga_mapping_file, os.path.join(archive_folder, "lga_mapping.csv")
            )

        except Exception as e:
            logging.error(f"Error loading LGA mapping data: {str(e)}")
            raise AirflowException(f"Failed to load LGA mapping data: {str(e)}")

    # Process NSW LGA code data
    nsw_lga_file = os.path.join(DIMENSIONS_DATA, "nsw_lga_code.csv")
    if os.path.exists(nsw_lga_file):
        logging.info("Loading NSW LGA code data...")
        try:
            df = pd.read_csv(nsw_lga_file)
            col_names = list(df.columns)
            values = df[col_names].to_dict("split")["data"]

            insert_sql = f"""
                INSERT INTO bronze.raw_nsw_lga_code({','.join(col_names)})
                VALUES %s
                ON CONFLICT DO NOTHING
            """

            result = execute_values(
                conn_ps.cursor(), insert_sql, values, page_size=1000
            )
            conn_ps.commit()
            logging.info(f"Successfully loaded {len(df)} rows from NSW LGA codes")

            # Archive file
            archive_folder = os.path.join(DIMENSIONS_DATA, "archive")
            if not os.path.exists(archive_folder):
                os.makedirs(archive_folder)
            shutil.move(nsw_lga_file, os.path.join(archive_folder, "nsw_lga_code.csv"))

        except Exception as e:
            logging.error(f"Error loading NSW LGA code data: {str(e)}")
            raise AirflowException(f"Failed to load NSW LGA code data: {str(e)}")

    logging.info("Census data load completed successfully")
    return None


def trigger_dbt_cloud_job(**kwargs):
    """
    Trigger dbt Cloud job to run the data transformation pipeline
    """
    logging.info("Triggering dbt Cloud job...")

    try:
        # Get the dbt Cloud configuration from Airflow Variables
        dbt_cloud_url = Variable.get("DBT_CLOUD_URL")
        dbt_cloud_account_id = Variable.get("DBT_CLOUD_ACCOUNT_ID")
        dbt_cloud_job_id = Variable.get("DBT_CLOUD_JOB_ID")
        dbt_cloud_token = Variable.get("DBT_CLOUD_API_TOKEN")

        # Define the URL for the dbt Cloud job API
        url = f"https://{dbt_cloud_url}/api/v2/accounts/{dbt_cloud_account_id}/jobs/{dbt_cloud_job_id}/run/"

        # Define the headers and body for the request
        headers = {
            "Authorization": f"Token {dbt_cloud_token}",
            "Content-Type": "application/json",
        }
        data = {"cause": "Triggered via Airflow - Airbnb Census Pipeline"}

        logging.info(f"Making request to dbt Cloud API: {url}")

        # Make the POST request to trigger the dbt Cloud job
        response = requests.post(url, headers=headers, json=data)

        # Check if the response is successful
        if response.status_code == 200:
            response_data = response.json()
            run_id = response_data.get("data", {}).get("id")
            logging.info(f"Successfully triggered dbt Cloud job. Run ID: {run_id}")

            # Store the run ID in XCom for potential use by other tasks
            kwargs["task_instance"].xcom_push(key="dbt_run_id", value=run_id)

            return response_data
        else:
            logging.error(
                f"Failed to trigger dbt Cloud job: {response.status_code}, {response.text}"
            )
            raise AirflowException(
                f"Failed to trigger dbt Cloud job: {response.status_code}"
            )

    except Exception as e:
        logging.error(f"Error triggering dbt Cloud job: {str(e)}")
        raise AirflowException(f"Failed to trigger dbt Cloud job: {str(e)}")


#########################################################
#
#   DAG Operator Setup
#
#########################################################

# Data loading task
load_airbnb_task = PythonOperator(
    task_id="load_airbnb_listings",
    python_callable=load_airbnb_listings_func,
    provide_context=True,
    dag=dag,
)

# dbt Cloud job trigger task
trigger_dbt_job_task = PythonOperator(
    task_id="trigger_dbt_cloud_job",
    python_callable=trigger_dbt_cloud_job,
    provide_context=True,
    dag=dag,
)

#########################################################
#
#   Task Dependencies
#
#########################################################

# Load Airbnb data, then trigger dbt
load_airbnb_task >> trigger_dbt_job_task
