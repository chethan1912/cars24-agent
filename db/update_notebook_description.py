import json
from pathlib import Path

path = Path('data/dataextract.ipynb')
nb = json.loads(path.read_text(encoding='utf-8'))

new_source = [
    "data['Description'] = (",
    "    data['Brand'].astype(str) + ' ' + ",
    "    data['model'].astype(str) + ' ' + ",
    "    data['Year'].astype(str) + ' model of ' + ",
    "    data['FuelType'].astype(str) + ' variant driven for ' + ",
    "    data['kmDriven'].astype(str) + ' in ' + ",
    "    data['City'].astype(str)",
    ")",
]

found = False
for cell in nb['cells']:
    if cell.get('cell_type') == 'code' and any("data['Description']=data['Brand'][0]" in line for line in cell.get('source', [])):
        cell['source'] = new_source
        found = True
        break

if not found:
    raise ValueError('Could not find the description generation cell.')

path.write_text(json.dumps(nb, indent=1), encoding='utf-8')
print('Notebook updated successfully')
