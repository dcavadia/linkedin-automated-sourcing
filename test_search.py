from app.nodes.search import search_linkedin
from pprint import pprint

# Your config (example)
config = {
    'keywords': ['AI Engineer'],
    'location': 'Venezuela',
    'company': 'NVIDIA',
    'min_exp': 0
}

profiles = search_linkedin(config)
print("Full Profiles (sorted by relevance_score):")
pprint(profiles)
print(f"\nTotal: {len(profiles)} candidates processed.")
