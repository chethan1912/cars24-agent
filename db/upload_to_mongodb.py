import pandas as pd
import ast
import numpy as np
import re
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError, PyMongoError

# MongoDB connection URI
import os
uri=os.getenv("uri")


def connect_to_mongodb():
    """Connect to MongoDB cluster."""
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


def load_and_preprocess_data(csv_path, num_rows=1000):
    """Load CSV and preprocess data."""
    try:
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded CSV with {len(df)} rows")

        # Take first 1000 rows
        df = df.head(num_rows)
        print(f"✓ Selected first {len(df)} rows")

        # Remove any rows with null values
        initial_count = len(df)
        df = df.dropna()
        print(
            f"✓ Dropped {initial_count - len(df)} rows with null values ({len(df)} remaining)")

        return df
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return None


def convert_embeddings(df):
    """Convert embeddings from NumPy array string representation to list of floats."""
    try:
        def parse_embedding(emb):
            if isinstance(emb, str):
                # Remove brackets from NumPy array string format: "[ 1.2 3.4 ... 5.6]"
                emb = emb.strip()
                # Remove leading and trailing brackets
                emb = emb.replace('[', '').replace(']', '')
                # Remove ellipsis and everything after it if present
                if '...' in emb:
                    emb = emb[:emb.index('...')]
                # Split by whitespace and filter empty strings
                numbers = [float(x) for x in emb.split() if x.strip()]
                return numbers
            elif isinstance(emb, list):
                return emb
            else:
                return None

        df['embeddings'] = df['embeddings'].apply(parse_embedding)

        # Verify conversion
        first_emb = df['embeddings'].iloc[0]
        if isinstance(first_emb, list) and len(first_emb) > 0:
            print(
                f"✓ Embeddings converted to list format (dimension: {len(first_emb)})")
        else:
            print(f"✗ Embeddings conversion failed")
            return False

        return True
    except Exception as e:
        print(f"✗ Error converting embeddings: {e}")
        return False


def upload_to_mongodb(client, df, db_name='cars24', collection_name='cars_available'):
    """Upload data to MongoDB."""
    try:
        db = client[db_name]
        collection = db[collection_name]

        # Convert DataFrame to list of dictionaries
        documents = df.to_dict(orient='records')

        # Insert documents
        result = collection.insert_many(documents, ordered=False)
        print(
            f"✓ Inserted {len(result.inserted_ids)} documents into {db_name}.{collection_name}")

        return True
    except PyMongoError as e:
        print(f"✗ MongoDB error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error uploading data: {e}")
        return False


def main():
    """Main execution function."""
    print("=" * 60)
    print("MongoDB Data Upload Script")
    print("=" * 60)

    # Step 1: Connect to MongoDB
    print("\n[1/4] Connecting to MongoDB...")
    client = connect_to_mongodb()
    if not client:
        return

    # Step 2: Load and preprocess CSV
    print("\n[2/4] Loading and preprocessing CSV...")
    csv_path = r"C:\Users\cheth\.cache\kagglehub\datasets\mohitkumar282\used-car-dataset\versions\3\used_car_dataset_with_embeddings.csv"
    df = load_and_preprocess_data(csv_path, num_rows=1000)
    if df is None or len(df) == 0:
        return

    # Step 3: Convert embeddings
    print("\n[3/4] Converting embeddings...")
    if not convert_embeddings(df):
        return

    # Step 4: Upload to MongoDB
    print("\n[4/4] Uploading to MongoDB...")
    if upload_to_mongodb(client, df):
        print("\n" + "=" * 60)
        print("✓ Upload completed successfully!")
        print("=" * 60)

    # Close connection
    client.close()


if __name__ == "__main__":
    main()
