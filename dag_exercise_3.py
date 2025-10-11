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
    'owner': 'BDE_LAB_6',
    'start_date': datetime.now() - timedelta(days=2+4),
    'email': [],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'depends_on_past': False,
    'wait_for_downstream': False,
}

dag = DAG(
    dag_id='exercise_3',
    default_args=dag_default_args,
    schedule_interval=None,
    catchup=True,
    max_active_runs=1,
    concurrency=5
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

def import_load_dim_category_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    category_file_path = DIMENSIONS + 'category.csv'
    if not os.path.exists(category_file_path):
        logging.info("No category.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(category_file_path)

    if len(df) > 0:
        col_names = ['id', 'category']
        values = df[col_names].to_dict('split')['data']
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_category(id, category)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, 'archive')
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(category_file_path, os.path.join(archive_folder, 'category.csv'))
    return None


def import_load_dim_sub_category_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    sub_category_file_path = DIMENSIONS + 'sub_category.csv'
    if not os.path.exists(sub_category_file_path):
        logging.info("No sub_category.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(sub_category_file_path)

    if len(df) > 0:
        col_names = ['id', 'sub_category']
        values = df[col_names].to_dict('split')['data']
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_subcategory(id, sub_category)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, 'archive')
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(sub_category_file_path, os.path.join(archive_folder, 'sub_category.csv'))
    return None


def import_load_dim_brand_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Check if the file exists
    brand_file_path = DIMENSIONS + 'brand.csv'
    if not os.path.exists(brand_file_path):
        logging.info("No brand.csv file found.")
        return None

    # Generate dataframe by reading the CSV file
    df = pd.read_csv(brand_file_path)

    if len(df) > 0:
        col_names = ['id', 'brand']
        values = df[col_names].to_dict('split')['data']
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_brand(id, brand)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move the processed file to the archive folder
        archive_folder = os.path.join(DIMENSIONS, 'archive')
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        shutil.move(brand_file_path, os.path.join(archive_folder, 'brand.csv'))
    return None


def import_load_facts_func(**kwargs):

    # Setup Postgres connection
    ps_pg_hook = PostgresHook(postgres_conn_id="postgres")
    conn_ps = ps_pg_hook.get_conn()

    # Get all files with '.csv' extension in the FACTS directory
    filelist = [k for k in os.listdir(FACTS) if '.csv' in k]

    # Check if there are any files to process
    if len(filelist) == 0:
        logging.info("No CSV files found in the FACTS directory.")
        return None  # Exit gracefully if no files are found

    # Generate dataframe by combining all files
    df = pd.concat([pd.read_csv(os.path.join(FACTS, fname)) for fname in filelist], ignore_index=True)

    if len(df) > 0:
        col_names = ['date', 'order_id', 'category_id', 'subcategory_id', 'brand_id', 'price']
        values = df[col_names].to_dict('split')['data']
        logging.info(values)

        insert_sql = """
                    INSERT INTO bronze.raw_facts(date, order_id, category_id, subcategory_id, brand_id, price)
                    VALUES %s
                    """
        result = execute_values(conn_ps.cursor(), insert_sql, values, page_size=len(df))
        conn_ps.commit()

        # Move processed files to the archive folder
        archive_folder = os.path.join(FACTS, 'archive')
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)

        for fname in filelist:
            shutil.move(os.path.join(FACTS, fname), os.path.join(archive_folder, fname))
    return None

#########################################################
#
#   Function to trigger dbt Cloud Job
#
#########################################################

def trigger_dbt_cloud_job(**kwargs):
    # Get the dbt Cloud URL, account ID, and job ID from Airflow Variables
    dbt_cloud_url = Variable.get("DBT_CLOUD_URL")
    dbt_cloud_account_id = Variable.get("DBT_CLOUD_ACCOUNT_ID")
    dbt_cloud_job_id = Variable.get("DBT_CLOUD_JOB_ID")
    
    # Define the URL for the dbt Cloud job API dynamically using URL, account ID, and job ID
    url = f"https://{dbt_cloud_url}/api/v2/accounts/{dbt_cloud_account_id}/jobs/{dbt_cloud_job_id}/run/"
    
    # Get the dbt Cloud API token from Airflow Variables
    dbt_cloud_token = Variable.get("DBT_CLOUD_API_TOKEN")
    
    # Define the headers and body for the request
    headers = {
        'Authorization': f'Token {dbt_cloud_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "cause": "Triggered via API"
    }
    
    # Make the POST request to trigger the dbt Cloud job
    response = requests.post(url, headers=headers, json=data)
    
    # Check if the response is successful
    if response.status_code == 200:
        logging.info("Successfully triggered dbt Cloud job.")
        return response.json()
    else:
        logging.error(f"Failed to trigger dbt Cloud job: {response.status_code}, {response.text}")
        raise AirflowException("Failed to trigger dbt Cloud job.")

#########################################################
#
#   DAG Operator Setup
#
#########################################################

import_load_dim_category_task = PythonOperator(
    task_id="import_load_dim_category_id",
    python_callable=import_load_dim_category_func,
    provide_context=True,
    dag=dag
)

import_load_dim_sub_category_task = PythonOperator(
    task_id="import_load_dim_sub_category_id",
    python_callable=import_load_dim_sub_category_func,
    provide_context=True,
    dag=dag
)

import_load_dim_brand_task = PythonOperator(
    task_id="import_load_dim_brand_id",
    python_callable=import_load_dim_brand_func,
    provide_context=True,
    dag=dag
)

import_load_facts_task = PythonOperator(
    task_id="import_load_facts_id",
    python_callable=import_load_facts_func,
    provide_context=True,
    dag=dag
)

trigger_dbt_job_task = PythonOperator(
    task_id='trigger_dbt_job',
    python_callable=trigger_dbt_cloud_job,
    provide_context=True,
    dag=dag
)

# Task Dependencies
[import_load_dim_category_task, import_load_dim_sub_category_task, import_load_dim_brand_task] >> import_load_facts_task >> trigger_dbt_job_task
