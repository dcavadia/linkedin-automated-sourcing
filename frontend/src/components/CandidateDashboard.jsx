import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const CandidateDashboard = () => {
  const [candidates, setCandidates] = useState([]); 
  const [interactions, setInteractions] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');

  // Fetch metrics (unchanged)
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await axios.get(`${API_BASE}/metrics`);
        setMetrics(res.data);
      } catch (err) {
        console.error('Metrics fetch failed:', err);
      }
    };
    fetchMetrics();
  }, []);

  // Fetch candidates & interactions
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const candRes = await axios.get(`${API_BASE}/candidates`);
        const sortedCandidates = candRes.data.sort((a, b) => b.relevance_score - a.relevance_score);
        setCandidates(sortedCandidates);

        const intRes = await axios.get(`${API_BASE}/interactions`);
        const aggregated = intRes.data.reduce((acc, interaction) => {
          const candId = interaction.candidate_id;  // linkedin_id
          if (!acc[candId]) {
            acc[candId] = {
              id: candId,
              name: interaction.candidate_name || 'Unknown',
              current_company: interaction.current_company || 'Unknown',
              messages_sent: 0,
              replies_received: 0
            };
          }
          acc[candId].messages_sent += 1;
          if (interaction.response) {
            acc[candId].replies_received += 1;
            if (!acc[candId].name || acc[candId].name === 'Unknown') {
              acc[candId].name = interaction.candidate_name || acc[candId].name;
            }
            if (!acc[candId].current_company || acc[candId].current_company === 'Unknown') {
              acc[candId].current_company = interaction.current_company || acc[candId].current_company;
            }
          }
          return acc;
        }, {});
        setInteractions(Object.values(aggregated));
      } catch (err) {
        alert('Failed to fetch data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredCandidates = candidates.filter(c =>
    c.name.toLowerCase().includes(filter.toLowerCase()) ||
    c.skills.toLowerCase().includes(filter.toLowerCase())
  );
  const filteredInteractions = interactions.filter(c =>
    c.name.toLowerCase().includes(filter.toLowerCase()) ||
    c.current_company.toLowerCase().includes(filter.toLowerCase())
  );

  const handleExport = () => {
    window.location.href = `${API_BASE}/export-report`;
  };

  return (
    <div style={{ maxWidth: 1000, margin: 'auto', padding: 20 }}>
      <h2>Candidate Dashboard</h2>
      
      {Object.keys(metrics).length > 0 && (
        <div style={{ 
          marginBottom: 20, 
          padding: 15, 
          backgroundColor: '#e8f4fd', 
          borderRadius: 8, 
          border: '1px solid #bee5eb' 
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#0c5460' }}>Overall Effectiveness Metrics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
            <p><strong>Total Messages Sent:</strong> {metrics.total_messages_sent}</p>
            <p><strong>Total Replies:</strong> {metrics.total_replies}</p>
            <p><strong>Reply Rate:</strong> {metrics.reply_rate_percent}%</p>
            <p><strong>Avg Response Time:</strong> {metrics.avg_response_time_days} days</p>
          </div>
        </div>
      )}
      
      <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
        <input
          type="text"
          placeholder="Search by name, skills, or company"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ flex: 1, padding: 8, border: '1px solid #ccc', borderRadius: 4 }}
        />
        <button 
          onClick={handleExport} 
          style={{ 
            padding: '8px 16px', 
            backgroundColor: '#007bff', 
            color: 'white', 
            border: 'none', 
            borderRadius: 4, 
            cursor: 'pointer' 
          }}
        >
          Download Report CSV
        </button>
      </div>
      
      <div style={{ marginBottom: 30 }}>
        <h3>Candidates Overview ({filteredCandidates.length}, Sorted by Relevance Score)</h3>
        {loading ? (
          <p>Loading candidates...</p>
        ) : filteredCandidates.length === 0 ? (
          <p>No candidates found{filter ? ` matching "${filter}"` : ''}.</p>
        ) : (
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 20 }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>Name</th>
                <th>Skills</th>
                <th>Relevance Score</th>
                <th>Search Date</th>
                <th>Profile URL</th>
              </tr>
            </thead>
            <tbody>
              {filteredCandidates.map((cand) => (
                <tr key={cand.id}>
                  <td>{cand.name}</td>
                  <td>{cand.skills}</td>
                  <td>{cand.relevance_score}/100</td>
                  <td>{new Date(cand.search_date).toLocaleString()}</td>
                  <td><a href={cand.profile_url} target="_blank" rel="noopener noreferrer">View</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div>
        <h3>Interactions by Candidate ({filteredInteractions.length})</h3>
        {loading ? (
          <p>Loading interactions...</p>
        ) : filteredInteractions.length === 0 ? (
          <p>No interactions found{filter ? ` matching "${filter}"` : ''}.</p>
        ) : (
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>Name</th>
                <th>Current Company</th>
                <th>Messages Sent</th>
                <th>Replies Received</th>
                <th>Reply Rate</th>
              </tr>
            </thead>
            <tbody>
              {filteredInteractions.map((cand) => (
                <tr key={cand.id}>
                  <td>{cand.name}</td>
                  <td>{cand.current_company}</td>
                  <td>{cand.messages_sent}</td>
                  <td>{cand.replies_received}</td>
                  <td>
                    {cand.messages_sent > 0 
                      ? ((cand.replies_received / cand.messages_sent) * 100).toFixed(1) + '%' 
                      : '0%'
                    }
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

export default CandidateDashboard;
