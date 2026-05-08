import os

import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import ast

# MongoDB connection
uri = os.getenv("uri")

print("=" * 70)
print("Fixing Truncated Embeddings in MongoDB")
print("=" * 70)

# Step 1: Check what's currently in MongoDB
print("\n[1/3] Checking current embeddings in MongoDB...")
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')
    collection = client['cars24']['cars_available']
    
    doc = collection.find_one()
    current_dim = len(doc['embeddings']) if doc and 'embeddings' in doc else 0
    print(f"✓ Current embedding dimension: {current_dim}")
except Exception as e:
    print(f"✗ Error: {e}")
    exit()

# Step 2: Load CSV and attempt to extract full embeddings
print("\n[2/3] Loading embeddings from CSV...")
csv_path = r"C:\Users\cheth\.cache\kagglehub\datasets\mohitkumar282\used-car-dataset\versions\3\used_car_dataset_with_embeddings.csv"

try:
    df = pd.read_csv(csv_path)
    df = df.head(1000)
    
    # The embeddings in CSV are stored as string representation
    # Even though truncated in display, let's try to parse all visible numbers
    def parse_full_embedding(emb_str):
        if not isinstance(emb_str, str):
            return None
        
        # Remove brackets
        emb_str = emb_str.strip().replace('[', '').replace(']', '')
        
        # Split by whitespace
        parts = emb_str.split()
        
        # Parse all numeric values (including those after and before ...)
        numbers = []
        for part in parts:
            if part != '...':
                try:
                    numbers.append(float(part))
                except:
                    pass
        
        return numbers if numbers else None
    
    print(f"✓ Loading {len(df)} records from CSV")
    embeddings_list = df['embeddings'].apply(parse_full_embedding).tolist()
    
    # Check dimension of first embedding
    first_dim = len(embeddings_list[0]) if embeddings_list[0] else 0
    print(f"✓ Parsed embeddings count from CSV: {first_dim}")
    
    # Step 3: Update MongoDB with parsed embeddings
    print("\n[3/3] Updating MongoDB with parsed embeddings...")
    
    # Clear collection
    collection.delete_many({})
    print("✓ Cleared collection")
    
    # Prepare documents
    documents = df.to_dict(orient='records')
    for i, doc in enumerate(documents):
        doc['embeddings'] = embeddings_list[i]
    
    # Insert
    result = collection.insert_many(documents, ordered=False)
    print(f"✓ Inserted {len(result.inserted_ids)} documents")
    
    # Verify
    sample = collection.find_one()
    sample_dim = len(sample['embeddings']) if sample and 'embeddings' in sample else 0
    print(f"✓ Updated embedding dimension: {sample_dim}")
    
    print("\n" + "=" * 70)
    if sample_dim >= 100:
        print("✓ Embeddings updated successfully!")
    else:
        print("⚠ Embeddings may still be truncated, consider regenerating from source")
    print("=" * 70)
    
    client.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
