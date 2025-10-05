import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const SearchModule = () => {
  const [config, setConfig] = useState({
    keywords: 'AI Engineer',  // String or array; backend joins
    location: 'Venezuela',
    company: '',
    min_exp: 2,
    max_results: 10  // Pass to search.py if you add limit there (e.g., profile_cards[:max_results])
  });
  const [results, setResults] = useState([]);
  const [savedCandidates, setSavedCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch saved candidates on load
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const res = await axios.get(`${API_BASE}/candidates`);
        setSavedCandidates(res.data);
      } catch (err) {
        console.error('Failed to load candidates:', err);
      }
    };
    fetchCandidates();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API_BASE}/search`, config);
      if (res.data.error) {
        setError(res.data.error);
      } else {
        setResults(res.data.profiles_found || []);
        setSavedCandidates(res.data.candidates || []);  // Update with new saved
      }
    } catch (err) {
      setError('Search failed: ' + err.message + '. Check console/backend logs.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (e) => {
    const { name, value } = e.target;
    setConfig({ ...config, [name]: name === 'keywords' ? value.split(' ') : value });  // Split keywords to array
    if (name === 'min_exp') setConfig({ ...config, [name]: parseInt(value) || 0 });
  };

  const handleGenerateMessage = (candidate) => {
    // Integrate with MessageGenerator: Pre-fill form with candidate data
    alert(`Generate message for ${candidate.name} (ID: ${candidate.id})\nExperience: ${candidate.experience_years} years ${candidate.skills.join(', ')}\nCompany: ${candidate.current_company}\n(Implement: Navigate to MessageGenerator with these values)`);
    // Todo: Use React Router or state to pass to MessageGenerator (e.g., set global state)
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>LinkedIn Search Module (Using search.py)</h2>
      <p>Configure filters and trigger search to find AI candidates. Results populate the DB pipeline.</p>
      
      {/* Filters Form (Grid Layout) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
        <input
          name="keywords"
          placeholder="Keywords (e.g., AI Engineer ML)"
          value={config.keywords}
          onChange={handleConfigChange}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <input
          name="location"
          placeholder="Location (e.g., Venezuela)"
          value={config.location}
          onChange={handleConfigChange}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <input
          name="company"
          placeholder="Current Company (e.g., Google)"
          value={config.company}
          onChange={handleConfigChange}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <input
          name="min_exp"
          type="number"
          placeholder="Min Experience Years (default 2)"
          value={config.min_exp}
          onChange={handleConfigChange}
          style={{ padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
      </div>
      
      <button 
        onClick={handleSearch} 
        disabled={loading}
        style={{ 
          padding: '10px 20px', 
          backgroundColor: loading ? '#6c757d' : '#28a745', 
          color: 'white', 
          border: 'none', 
          borderRadius: 4, 
          cursor: loading ? 'not-allowed' : 'pointer', 
          marginBottom: 20 
        }}
      >
        {loading ? 'Searching LinkedIn...' : 'Start Search'}
      </button>
      
      {error && <p style={{ color: 'red', marginBottom: 10 }}>{error}</p>}
      
      {/* Search Results Table */}
      {results.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3>Search Results ({results.length} Found)</h3>
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>Name</th>
                <th>Skills</th>
                <th>Experience (Years)</th>
                <th>Location</th>
                <th>Current Company</th>
                <th>Profile URL</th>
              </tr>
            </thead>
            <tbody>
              {results.map((profile, idx) => (
                <tr key={idx}>
                  <td>{profile.name}</td>
                  <td>{Array.isArray(profile.skills) ? profile.skills.join(', ') : profile.skills}</td>
                  <td>{profile.experience_years}</td>
                  <td>{profile.location}</td>
                  <td>{profile.current_company}</td>
                  <td><a href={profile.profile_url} target="_blank" rel="noopener noreferrer">View</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Saved Candidates Table (From DB) */}
      <div>
        <h3>Saved Candidates in Pipeline ({savedCandidates.length})</h3>
        {savedCandidates.length === 0 ? (
          <p>No candidates saved yet. Run a search!</p>
        ) : (
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>ID</th>
                <th>Name</th>
                <th>Skills</th>
                <th>Experience</th>
                <th>Location</th>
                <th>Company</th>
                <th>Search Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {savedCandidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td>{candidate.id}</td>
                  <td>{candidate.name}</td>
                  <td>{candidate.skills}</td>
                  <td>{candidate.experience_years}</td>
                  <td>{candidate.location}</td>
                  <td>{candidate.current_company}</td>
                  <td>{new Date(candidate.search_date).toLocaleString()}</td>
                  <td>
                    <button 
                      onClick={() => handleGenerateMessage(candidate)} 
                      style={{ padding: '4px 8px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: 2 }}
                    >
                      Generate Message
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default SearchModule;
