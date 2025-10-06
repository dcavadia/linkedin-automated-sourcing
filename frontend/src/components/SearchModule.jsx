import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';
const DEFAULT_ROLE_DESC = "AI Engineer role at our innovative startup, focusing on ML pipelines and computer vision.";
const DEFAULT_CTA = "Please reply if interested in discussing this opportunity further.";

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

  // Message Gen State (Inline per Candidate)
  const [showGenForm, setShowGenForm] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [genCandidate, setGenCandidate] = useState({ id: '', name: '', experience: '', current_company: '' });
  const [roleDesc, setRoleDesc] = useState(DEFAULT_ROLE_DESC);
  const [cta, setCta] = useState(DEFAULT_CTA);
  const [genMessage, setGenMessage] = useState('');
  const [genLoading, setGenLoading] = useState(false);

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

  const handleGenerateMessage = (profile) => {
    // Pre-fill form with simplified data from profile
    const exp = `AI Engineer based on skills: ${Array.isArray(profile.skills) ? profile.skills.join(', ') : profile.skills}`;
    setGenCandidate({
      id: profile.id || profile.linkedin_id,
      name: profile.name,
      experience: exp,
      current_company: 'N/A'  // Simplified
    });
    setRoleDesc(DEFAULT_ROLE_DESC);
    setCta(DEFAULT_CTA);
    setGenMessage('');
    setSelectedCandidate(profile);
    setShowGenForm(true);
  };

  const submitGenerate = async () => {
    if (!genCandidate.id || !genCandidate.name) {
      alert('Candidate data incomplete.');
      return;
    }
    setGenLoading(true);
    try {
      const postData = {
        ...genCandidate,
        role_desc: roleDesc,
        cta: cta
      };
      const res = await axios.post(`${API_BASE}/generate`, postData);
      setGenMessage(res.data.message);
      alert(`Message generated and saved for ${genCandidate.name}! Track in Dashboard.`);
      setShowGenForm(false);  // Hide form
    } catch (err) {
      alert('Error generating message: ' + err.response?.data?.detail || err.message);
    } finally {
      setGenLoading(false);
    }
  };

  const cancelGen = () => {
    setShowGenForm(false);
    setGenMessage('');
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>LinkedIn Search Module (Using search.py)</h2>
      <p>Configure filters and trigger search to find AI candidates. Click "Generate Message" to personalize outreach.</p>
      
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
                <th>Actions</th>
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
                  <td>
                    <button 
                      onClick={() => handleGenerateMessage(profile)} 
                      style={{ padding: '4px 8px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: 2 }}
                    >
                      Generate Message
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Inline Message Gen Form (Per Candidate) */}
      {showGenForm && selectedCandidate && (
        <div style={{ backgroundColor: '#f9f9f9', padding: 20, borderRadius: 8, marginTop: 20 }}>
          <h3>Generate Message for {genCandidate.name}</h3>
          <p><strong>Pre-filled Data:</strong> ID: {genCandidate.id} | Experience: {genCandidate.experience} | Company: {genCandidate.current_company}</p>
          <div style={{ marginBottom: 10 }}>
            <label>Brief Role Description:</label>
            <textarea
              value={roleDesc}
              onChange={(e) => setRoleDesc(e.target.value)}
              placeholder="e.g., AI Engineer focusing on computer vision and ML pipelines"
              style={{ width: '100%', height: 80, padding: 8, border: '1px solid #ccc', borderRadius: 4, marginTop: 5 }}
            />
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>Clear Call to Action:</label>
            <input
              type="text"
              value={cta}
              onChange={(e) => setCta(e.target.value)}
              placeholder="e.g., Reply to schedule a quick call"
              style={{ width: '100%', padding: 8, border: '1px solid #ccc', borderRadius: 4, marginTop: 5 }}
            />
          </div>
          <button 
            onClick={submitGenerate} 
            disabled={genLoading}
            style={{ padding: '8px 16px', backgroundColor: genLoading ? '#6c757d' : '#28a745', color: 'white', border: 'none', borderRadius: 4, marginRight: 10 }}
          >
            {genLoading ? 'Generating...' : 'Generate & Save'}
          </button>
          <button onClick={cancelGen} style={{ padding: '8px 16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: 4 }}>
            Cancel
          </button>
          {genMessage && (
            <div style={{ marginTop: 20, padding: 15, backgroundColor: 'white', border: '1px solid #ddd', borderRadius: 4 }}>
              <h4>Generated Message:</h4>
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{genMessage}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchModule;
