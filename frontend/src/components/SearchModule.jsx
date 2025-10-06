import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const SearchModule = () => {
  const [config, setConfig] = useState({
    keywords: 'AI Engineer',  // String; split to array in handleSearch
    location: 'Venezuela',
    company: '',
    min_exp: 2,
    max_results: 10  // Optional
  });
  const [results, setResults] = useState([]);  // Full profiles from search
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch saved candidates on load (for potential use, but not displayed)
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const res = await axios.get(`${API_BASE}/candidates`);
        // Sort by relevance_score DESC (not displayed)
        const sorted = res.data.sort((a, b) => b.relevance_score - a.relevance_score);
        // Keep for future, but no UI
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
      // Prepare config: Split keywords to array
      const configData = {
        ...config,
        keywords: config.keywords.split(' ').filter(Boolean)  // e.g., "AI Engineer ML" → ["AI", "Engineer", "ML"]
      };
      const res = await axios.post(`${API_BASE}/search`, configData);
      if (res.data.error) {
        setError(res.data.error);
      } else {
        // Sort results by score DESC
        const sortedResults = (res.data.profiles_found || []).sort((a, b) => b.relevance_score - a.relevance_score);
        setResults(sortedResults);
      }
    } catch (err) {
      setError('Search failed: ' + err.response?.data?.detail || err.message + '. Check console/backend logs.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (e) => {
    const { name, value } = e.target;
    setConfig({ ...config, [name]: name === 'min_exp' ? parseInt(value) || 0 : value });
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>LinkedIn Search Module (Using search.py)</h2>
      <p>Configure filters and trigger search to find AI candidates. Results are saved to database. Use the Message Generator module for personalized outreach.</p>
      
      {/* Filters Form (Grid Layout) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 20 }}>
        <input
          name="keywords"
          placeholder="Keywords (space-sep, e.g., AI Engineer ML)"
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
      
      {/* Search Results Table (Full Profiles for Preview, Minimal Columns) */}
      {results.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h3>Search Results ({results.length} Found, Sorted by Score)</h3>
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>Name</th>
                <th>Skills</th>
                <th>Relevance Score</th>
                <th>Location</th>
                <th>Profile URL</th>
              </tr>
            </thead>
            <tbody>
              {results.map((profile, idx) => (
                <tr key={idx}>
                  <td>{profile.name}</td>
                  <td>{Array.isArray(profile.skills) ? profile.skills.join(', ') : profile.skills}</td>
                  <td>{profile.relevance_score}/100</td>
                  <td>{profile.location}</td>
                  <td><a href={profile.profile_url} target="_blank" rel="noopener noreferrer">View</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default SearchModule;
