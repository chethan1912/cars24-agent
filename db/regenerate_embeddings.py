import pandas as pd
import os
from huggingface_hub import InferenceClient
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
import os
uri=os.getenv("uri")

# HuggingFace client
client = InferenceClient(
    provider="hf-inference",
    api_key=os.environ.get("hf_token"),
)


def regenerate_embeddings_and_upload():
    """Regenerate full embeddings and upload to MongoDB."""

    print("=" * 70)
    print("Regenerating Full Embeddings (768 dimensions) and Uploading to MongoDB")
    print("=" * 70)

    # Step 1: Load data
    print("\n[1/4] Loading CSV data...")
    csv_path = r"C:\Users\cheth\.cache\kagglehub\datasets\mohitkumar282\used-car-dataset\versions\3\used_car_dataset_with_embeddings.csv"
    df = pd.read_csv(csv_path)
    df = df.head(1000)
    df = df.dropna()
    print(f"✓ Loaded {len(df)} rows")

    # Step 2: Generate embeddings
    print("\n[2/4] Generating full embeddings from HuggingFace...")
    batch_size = 32
    all_embeddings = []

    for i in range(0, len(df), batch_size):
        batch_data = df['description'].iloc[i: i + batch_size].tolist()

        print(
            f"  Processing batch {i//batch_size + 1}/{(len(df) + batch_size - 1)//batch_size}...", end='\r')

        try:
            # Get embeddings from HuggingFace
            embeddings_list = client.feature_extraction(
                batch_data,
                model="microsoft/harrier-oss-v1-0.6b",
            )

            # Convert to list of lists (full 768 dimensions)
            if hasattr(embeddings_list, 'tolist'):
                embeddings_as_list = embeddings_list.tolist()
            else:
                embeddings_as_list = [list(e) for e in embeddings_list]

            all_embeddings.extend(embeddings_as_list)
        except Exception as e:
            print(f"\n✗ Error generating embeddings: {e}")
            return False

    print(f"\n✓ Generated {len(all_embeddings)} embeddings")

    # Verify embedding dimensions
    if len(all_embeddings) > 0:
        emb_dim = len(all_embeddings[0])
        print(f"✓ Embedding dimension: {emb_dim}")

    # Step 3: Connect to MongoDB
    print("\n[3/4] Connecting to MongoDB...")
    try:
        mongo_client = MongoClient(uri, server_api=ServerApi('1'))
        mongo_client.admin.command('ping')
        print("✓ Connected to MongoDB!")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

    # Step 4: Upload to MongoDB
    print("\n[4/4] Uploading to MongoDB...")
    try:
        db = mongo_client['cars24']

        # Drop existing collection to avoid duplicates
        db['cars_available'].drop()
        print("✓ Cleared existing collection")

        collection = db['cars_available']

        # Prepare documents
        documents = df.to_dict(orient='records')

        # Add embeddings to each document
        for i, doc in enumerate(documents):
            doc['embeddings'] = all_embeddings[i]

        # Insert all documents
        result = collection.insert_many(documents, ordered=False)
        print(f"✓ Inserted {len(result.inserted_ids)} documents")

        # Verify one document
        sample_doc = collection.find_one()
        if sample_doc and 'embeddings' in sample_doc:
            print(
                f"✓ Sample embedding dimension: {len(sample_doc['embeddings'])}")

        print("\n" + "=" * 70)
        print("✓ Upload completed successfully!")
        print("✓ All embeddings are now 768-dimensional")
        print("=" * 70)

        mongo_client.close()
        return True

    except Exception as e:
        print(f"✗ Error uploading: {e}")
        return False


if __name__ == "__main__":
    regenerate_embeddings_and_upload()
