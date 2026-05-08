import pandas as pd
import numpy as np

path = r"C:\Users\cheth\.cache\kagglehub\datasets\mohitkumar282\used-car-dataset\versions\3\used_car_dataset_with_embeddings.csv"
df = pd.read_csv(path, nrows=2)

print("Sample embedding (first 150 chars):")
sample = df['embeddings'].iloc[0]
print(repr(sample[:150]))
print("\nFull length:", len(sample))
print("Type stored:", type(sample))

# Try to identify the pattern
if '[' in sample and ']' in sample:
    print("Format: List-like string")
    # Check for numpy array format
    if '.e-' in sample or '.e+' in sample:
        print("Contains scientific notation (NumPy format)")
