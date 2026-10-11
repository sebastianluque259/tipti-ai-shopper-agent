import os
import json
import requests
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from openai import OpenAI
from dotenv import load_dotenv 
from settings import PROJECT_ROOT, GOOGLE_CREDENTIALS_PATH, OPENAI_API_KEY


# --- Access to .env ---
load_dotenv()
username = os.getenv("TIPTI_USERNAME")
password = os.getenv("TIPTI_PASSWORD")
api_url = os.getenv("API_URL")

# --- Authentication via Token for Private Tipti API calls ---
def get_auth_token():
    """Retrieves the authentication token from the API with retry logic."""

    # Payload and header for request
    url = f"{api_url}/auth/login"
    headers = {"accept": "/", 
               "Content-Type": "application/x-www-form-urlencoded"
               }
    data = {
        "username": username,
        "password": password
    }
    error_message = ""
    r = None

    # Request
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, data=data)
            r.raise_for_status()
            return r.json().get('access_token')
        except requests.exceptions.RequestException as e:
            error_message = f"Attempt {attempt + 1} failed: {e}"
            print(error_message)

    print(f"Failed to get authentication token after 3 attempts. Last error: {error_message}")
    return None 


# =========================================
# Tool: retailer_id search by retailer_name
# =========================================

def get_retailer_id(word: str):
    """Returns a list with the retailer_id, retailer_name, and embedding vector, corresponding to the user input"""

    # OpenAI API Client Initialization
    gpt_client = OpenAI(api_key=OPENAI_API_KEY)

    # BigQuery Client Initialization
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH
    )
    big_query_client = bigquery.Client(credentials=credentials)

    # Transforms input word to embeddings using OpenAI API
    model="text-embedding-3-small"
    dimensions=256
    embedding = gpt_client.embeddings.create(input=[word], model=model, dimensions=dimensions).data[0].embedding
    key_vector = ', '.join(f"{x}" for x in embedding)

    # Query for embedding matching in BigQuery via cosine similarity
    num_results = 5
    threshold = 0.43

    try:
        sql = f"""
        WITH input_vector AS (
            SELECT ARRAY<FLOAT64>[{key_vector}] AS query_embedding
        )
        SELECT 
            retailer_id,
            retailer_name,
            1 - ML.DISTANCE(query_embedding, embedding_vector, 'COSINE') AS cosine_similarity
        FROM CATALOG.misuper_retail_embeddings_array, input_vector
        WHERE 1 - ML.DISTANCE(query_embedding, embedding_vector, 'COSINE') > {threshold}
        ORDER BY cosine_similarity DESC
        LIMIT {num_results}
        """

        similar_retailers = big_query_client.query(sql)
        rows = [dict(row) for row in similar_retailers]  # Converting results to a list of dictionaries
        similar_retailers_df = pd.DataFrame(rows)

        if similar_retailers_df.empty: 
            return "No matching retailers found."
        else:
            results_list = similar_retailers_df.to_dict(orient='records')
            print(f"results: {results_list}")
            return results_list

    except Exception as e:
        return "Data extraction error."


# ============================================
# Tool: Manage product activation/deactivation
# ============================================

def manage_product(action: str, retailer_id: int, ean: str, reason: str):
    """Calls the endpoint /services/activate-deactivate-product to activate or deactivate a product."""

    auth_token = get_auth_token()

    # Check for correct token extraction
    if not auth_token:
        print("Error: Could not retrieve authentication token. Cannot proceed with API call.")
        return None 

    # Payload and header for request
    url = f"{api_url}/services/activate-deactivate-product"
    data = {
            "accion": action,
            "retailer_id": retailer_id,
            "ean": ean,
            "motivo": reason
            }
    headers = {"accept": "application/json",
            "Authorization": f"Bearer {auth_token}"
               }
    
    # Request
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Product management error (API call failed): {e}")
        if response is not None:
            print(f"Response content: {response.text}")
        return None
    

# ===============================
# Tool: Activate Fixed Bulk Price
# ===============================

def process_fixed_bulk(ean: str, avg_weight: int, price_per_kilo: int):
    """Calls the endpoint /services/procesar-bulk-fijo to activate a product as bulk."""

    auth_token = get_auth_token()

    # Check for correct token extraction
    if not auth_token:
        print("Error: Could not retrieve authentication token. Cannot proceed with API call.")
        return None 

    # Payload and header for request
    url = f"{api_url}/services/procesar-bulk-fijo"
    data = {
            "ean": ean,
            "peso_promedio": avg_weight,
            "precio_por_kilo": price_per_kilo,
            }
    headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {auth_token}"
            }
    
    # Request
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error activating Bulk product: {e}")
        if response is not None:
            print(f"Response content: {response.text}")
        return None

