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
        alert(`Found ${sortedResults.length} candidates – saved to DB! 🔍 Use Message Generator next.`);
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

  // New: Helper to generate concise breakdown tooltip
  const getBreakdownTooltip = (breakdown) => {
    if (!breakdown || typeof breakdown !== 'object') return '';
    const { keywords = 0, location = 0, company = 0, experience = 0, total } = breakdown;
    return `Keywords:${keywords} + Location:${location} + Company:${company} + Experience:${experience} = ${total}`;
  };

  return (
    <div style={{ maxWidth: 800, margin: 0 }}>
      <h2 style={{ color: '#495057', marginBottom: 20 }}>🔍 LinkedIn Candidate Search</h2>
      <p style={{ color: '#6c757d', marginBottom: 20 }}>Search for AI talent and save results to your database. Results auto-save for use in other modules.</p>
      
      {/* Filters Form (Grid Layout) */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: 10, 
        marginBottom: 20, 
        backgroundColor: '#fff', 
        padding: 20, 
        borderRadius: 8, 
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        border: '1px solid #e9ecef'
      }}>
        <input
          name="keywords"
          placeholder="Keywords (space-sep, e.g., AI Engineer ML)"
          value={config.keywords}
          onChange={handleConfigChange}
          style={{ padding: 12, border: '1px solid #dee2e6', borderRadius: 6, fontSize: '14px' }}
        />
        <input
          name="location"
          placeholder="Location (e.g., Venezuela)"
          value={config.location}
          onChange={handleConfigChange}
          style={{ padding: 12, border: '1px solid #dee2e6', borderRadius: 6, fontSize: '14px' }}
        />
        <input
          name="company"
          placeholder="Current Company (e.g., Google)"
          value={config.company}
          onChange={handleConfigChange}
          style={{ padding: 12, border: '1px solid #dee2e6', borderRadius: 6, fontSize: '14px' }}
        />
        <input
          name="min_exp"
          type="number"
          placeholder="Min Experience Years (default 2)"
          value={config.min_exp}
          onChange={handleConfigChange}
          style={{ padding: 12, border: '1px solid #dee2e6', borderRadius: 6, fontSize: '14px' }}
        />
      </div>
      
      <button 
        onClick={handleSearch} 
        disabled={loading}
        style={{ 
          padding: '12px 24px', 
          backgroundColor: loading ? '#6c757d' : '#007bff', 
          color: 'white', 
          border: 'none', 
          borderRadius: 6, 
          cursor: loading ? 'not-allowed' : 'pointer', 
          fontSize: '16px',
          marginBottom: 20 
        }}
      >
        {loading ? 'Searching LinkedIn...' : 'Start Search 🔍'}
      </button>
      
      {error && <p style={{ color: '#dc3545', marginBottom: 20, padding: 10, backgroundColor: '#f8d7da', borderRadius: 6, border: '1px solid #f5c6cb' }}>{error}</p>}
      
      {/* Search Results Table */}
      {results.length > 0 && (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef'
        }}>
          <h3 style={{ color: '#495057', marginBottom: 15 }}>Search Results ({results.length} Found, Sorted by Score)</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Name</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Skills</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Relevance Score</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Location</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Profile URL</th>
                </tr>
              </thead>
              <tbody>
                {results.map((profile, idx) => {
                  const tooltip = getBreakdownTooltip(profile.score_breakdown);  // New: Get tooltip
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                      <td style={{ padding: 12 }}>{profile.name}</td>
                      <td style={{ padding: 12 }}>{Array.isArray(profile.skills) ? profile.skills.join(', ') : profile.skills}</td>
                      <td style={{ padding: 12 }}>
                        {/* Updated: Add title tooltip for breakdown summary */}
                        <span 
                          title={tooltip} 
                          style={{ 
                            cursor: 'help', 
                            fontWeight: 'bold',
                            position: 'relative',
                            display: 'inline-flex',
                            alignItems: 'center'
                          }}
                        >
                          {profile.relevance_score}/100
                          <span style={{ marginLeft: '4px', fontSize: '12px' }}>ℹ️</span>  {/* Visual cue */}
                        </span>
                      </td>
                      <td style={{ padding: 12 }}>{profile.location}</td>
                      <td style={{ padding: 12 }}>
                        <a 
                          href={profile.profile_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ color: '#007bff', textDecoration: 'none' }}
                        >
                          View 🔗
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {results.length === 0 && !loading && <p style={{ color: '#6c757d', textAlign: 'center', padding: 40 }}>No results yet. Start a search! 🚀</p>}
    </div>
  );
};

export default SearchModule;
