#!/usr/bin/env python3
"""
dbt Cloud API Test Script
Use this to test your dbt Cloud API configuration before running Airflow
"""

import requests
import json


def test_dbt_cloud_api():
    print("🧪 TESTING dbt CLOUD API CONFIGURATION")
    print("=" * 50)

    # Get your values from Airflow Variables or set them here for testing
    DBT_CLOUD_URL = "tk735.us1.dbt.com"
    DBT_CLOUD_ACCOUNT_ID = "70471823499276"  # Replace with your actual account ID
    DBT_CLOUD_JOB_ID = "70471823519502"  # Replace with your actual job ID
    DBT_CLOUD_API_TOKEN = "dbtu_CNO3XA0XGyn3Q55pcf-w_GwEzV3bbg3FL-5kgIqK06jBBuNhyw"

    print(f"🔗 URL: {DBT_CLOUD_URL}")
    print(f"🏢 Account ID: {DBT_CLOUD_ACCOUNT_ID}")
    print(f"⚙️ Job ID: {DBT_CLOUD_JOB_ID}")
    print(
        f"🔑 Token: {DBT_CLOUD_API_TOKEN[:10]}..."
        if len(DBT_CLOUD_API_TOKEN) > 10
        else "❌ Token not set"
    )
    print()

    # Construct the URL
    url = f"https://{DBT_CLOUD_URL}/api/v2/accounts/{DBT_CLOUD_ACCOUNT_ID}/jobs/{DBT_CLOUD_JOB_ID}/run/"
    print(f"🎯 Full URL: {url}")
    print()

    # Set up headers exactly like the lab
    headers = {
        "Authorization": f"Token {DBT_CLOUD_API_TOKEN}",
        "Content-Type": "application/json",
    }

    data = {"cause": "Test API call"}

    print("📤 REQUEST DETAILS:")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    print()

    try:
        print("🚀 Making API request...")
        response = requests.post(url, headers=headers, json=data)

        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Text: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS! API call worked")
            response_data = response.json()
            print(f"🎉 Run ID: {response_data.get('data', {}).get('id')}")
        else:
            print("❌ FAILED! Check the error details above")

    except Exception as e:
        print(f"💥 ERROR: {str(e)}")


if __name__ == "__main__":
    test_dbt_cloud_api()
