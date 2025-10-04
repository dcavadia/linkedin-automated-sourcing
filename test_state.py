from app.state import AppState, Candidate

# Create sample state
config = {"keywords": ["AI", "ML", "Python"], "min_exp": 3, "location": "Remote"}
state = AppState(config=config)

# Add a mock candidate
mock_profile = {"name": "Jane Doe", "skills": ["ML Engineer"], "experience_years": 5}
state.candidates.append(Candidate(linkedin_id="mock123", profile_data=mock_profile, relevance_score=0.85))

print(state.model_dump_json(indent=2))  # Pretty-print to console
