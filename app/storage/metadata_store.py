import json
import os
from typing import List, Dict, Any

METADATA_FILE = "document_metadata.json"

# Ensure file exists
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, "w") as f:
        json.dump([], f)

def load_metadata() -> List[Dict[str, Any]]:
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def save_metadata(data: List[Dict[str, Any]]):
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
