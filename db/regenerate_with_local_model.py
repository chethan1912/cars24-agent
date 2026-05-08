import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from sentence_transformers import SentenceTransformer
import torch

# Check for GPU availability
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# MongoDB connection
import os
uri=os.getenv("uri")

print("=" * 70)
print("Regenerating Full Embeddings using Sentence Transformers")
print("=" * 70)

# Step 1: Load top rows only
print("\n[1/4] Loading CSV data...")
csv_path = r"C:\Users\cheth\.cache\kagglehub\datasets\mohitkumar282\used-car-dataset\versions\3\used_car_dataset_with_embeddings.csv"
NUM_ROWS = 1000

try:
    df = pd.read_csv(csv_path)
    df = df.head(NUM_ROWS)
    df = df.dropna()
    print(f"✓ Loaded {len(df)} rows (top {NUM_ROWS})")
except Exception as e:
    print(f"✗ Error loading CSV: {e}")
    exit()

# Step 2: Load embedding model
print("\n[2/4] Loading embedding model...")
try:
    # Using a local model for faster processing and to avoid API calls
    model = SentenceTransformer('all-mpnet-base-v2', device=device)
    print("✓ Loaded SentenceTransformer model")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    exit()

# Step 3: Generate embeddings
print("\n[3/4] Generating embeddings from descriptions...")
try:
    descriptions = df['description'].tolist()
    embeddings = model.encode(
        descriptions, batch_size=32, show_progress_bar=True, convert_to_numpy=True)

    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"✓ Embedding dimension: {len(embeddings[0])}")

    # Convert to list format
    embeddings_list = [embedding.tolist() for embedding in embeddings]
except Exception as e:
    print(f"✗ Error generating embeddings: {e}")
    exit()

# Step 4: Upload to MongoDB
print("\n[4/4] Uploading to MongoDB...")
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    client.admin.command('ping')
    print("✓ Connected to MongoDB")

    collection = client['cars24']['cars_available']

    # Clear existing collection
    collection.delete_many({})
    print("✓ Cleared collection")

    # Prepare documents with embeddings
    documents = df.to_dict(orient='records')
    for i, doc in enumerate(documents):
        doc['embeddings'] = embeddings_list[i]

    # Insert documents
    result = collection.insert_many(documents, ordered=False)
    print(f"✓ Inserted {len(result.inserted_ids)} documents")

    # Verify
    sample = collection.find_one()
    if sample and 'embeddings' in sample:
        print(f"✓ Sample embedding dimension: {len(sample['embeddings'])}")

    print("\n" + "=" * 70)
    print("✓ Upload completed successfully!")
    print(f"✓ All embeddings are now {len(embeddings_list[0])}-dimensional")
    print("=" * 70)

    client.close()

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
