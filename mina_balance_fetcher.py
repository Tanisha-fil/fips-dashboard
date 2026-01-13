import requests
import csv
import json
import time
from typing import List, Dict

# Configuration
MINA_GRAPHQL_URL = "https://graphql.minaexplorer.com/"  # Mina Explorer GraphQL API endpoint
OUTPUT_FILE = "mina_addresses_balances.csv"
BATCH_SIZE = 10  # Number of records per query (reduced for stability)

def fetch_accounts(limit: int = BATCH_SIZE, offset: int = 0, max_retries: int = 3) -> Dict:
    """Fetch accounts from Mina GraphQL endpoint with retry logic"""
    query = """
    query GetAccounts($limit: Int!, $offset: Int!) {
      staking(limit: $limit, offset: $offset) {
        public_key
        balance
      }
    }
    """
    
    variables = {
        "limit": limit,
        "offset": offset
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                MINA_GRAPHQL_URL,
                json={"query": query, "variables": variables},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching accounts (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in 5 seconds...")
                time.sleep(5)
            else:
                return None

def export_to_csv(all_accounts: List[Dict], filename: str):
    """Export accounts to CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Address', 'Balance (MINA)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for account in all_accounts:
                # Convert balance from nanomina to MINA (1 MINA = 1e9 nanomina)
                balance_mina = float(account['balance']) / 1e9
                writer.writerow({
                    'Address': account['public_key'],
                    'Balance (MINA)': f"{balance_mina:.9f}"
                })
        
        print(f"Successfully exported {len(all_accounts)} accounts to {filename}")
    except IOError as e:
        print(f"Error writing to file: {e}")

def main():
    """Main function to fetch and export all accounts"""
    print("Starting Mina address and balance export...")
    
    all_accounts = []
    offset = 0
    has_more = True
    
    while has_more:
        print(f"Fetching accounts at offset {offset}...")
        result = fetch_accounts(limit=BATCH_SIZE, offset=offset)
        
        if result is None or "errors" in result:
            error_msg = result.get("errors", [{}])[0].get("message", "Unknown error") if result else "No response"
            print(f"Error fetching data: {error_msg}")
            break
        
        accounts = result.get("data", {}).get("staking", [])
        
        if not accounts:
            has_more = False
            print("Reached end of accounts")
        else:
            all_accounts.extend(accounts)
            print(f"Fetched {len(accounts)} accounts (Total: {len(all_accounts)})")
            offset += BATCH_SIZE
            # Add a small delay between requests to be respectful to the API
            time.sleep(1)
    
    if all_accounts:
        export_to_csv(all_accounts, OUTPUT_FILE)
    else:
        print("No accounts found to export")

if __name__ == "__main__":
    main()
