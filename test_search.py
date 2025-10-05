from app.nodes.search import search_linkedin

config = {"keywords": ["AI Engineer"], "location": "Venezuela", "company": "NVIDIA", "min_exp": 0}
profiles = search_linkedin(config)
print("Profiles:", [p['name'] for p in profiles])
