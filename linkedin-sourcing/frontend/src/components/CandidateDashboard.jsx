import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const CandidateDashboard = () => {
  const [candidates, setCandidates] = useState([]);
  const [metrics, setMetrics] = useState({});  // Overall stats
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');  // For search

  // Fetch metrics (unchanged)
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await axios.get(`${API_BASE}/metrics`);
        setMetrics(res.data);
      } catch (err) {
        console.error('Metrics fetch failed:', err);  // Silent fail; dashboard still works
      }
    };
    fetchMetrics();
  }, []);

  // Fetch candidates (unchanged)
  useEffect(() => {
    const fetchCandidates = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`${API_BASE}/interactions`);
        // Aggregate interactions by candidate_id (unchanged)
        const aggregated = res.data.reduce((acc, interaction) => {
          const candId = interaction.candidate_id;
          if (!acc[candId]) {
            acc[candId] = {
              id: candId,
              name: interaction.candidate_name || 'Unknown',  // Use first non-null
              current_company: interaction.current_company || 'Unknown',
              messages_sent: 0,
              replies_received: 0
            };
          }
          acc[candId].messages_sent += 1;
          if (interaction.response) {
            acc[candId].replies_received += 1;
            // Update name/company if current is null (improve old data display)
            if (!acc[candId].name || acc[candId].name === 'Unknown') {
              acc[candId].name = interaction.candidate_name || acc[candId].name;
            }
            if (!acc[candId].current_company || acc[candId].current_company === 'Unknown') {
              acc[candId].current_company = interaction.current_company || acc[candId].current_company;
            }
          }
          return acc;
        }, {});
        setCandidates(Object.values(aggregated));
      } catch (err) {
        alert('Failed to fetch candidates: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, []);

  // Filter candidates by search term (name or company) (unchanged)
  const filteredCandidates = candidates.filter(c =>
    c.name.toLowerCase().includes(filter.toLowerCase()) ||
    c.current_company.toLowerCase().includes(filter.toLowerCase())
  );

  // New: Handle CSV download
  const handleExport = () => {
    window.location.href = `${API_BASE}/export-report`;
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>Candidate Dashboard</h2>
      
      {/* Metrics Summary Card (unchanged) */}
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
      
      {/* Updated: Search + Export Button Row */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
        <input
          type="text"
          placeholder="Search by name or company"
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
      
      {/* Existing: Table */}
      {loading ? (
        <p>Loading candidates...</p>
      ) : filteredCandidates.length === 0 ? (
        <p>No candidates found{filter ? ` matching "${filter}"` : ''}.</p>
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
            {filteredCandidates.map((cand) => (
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
  );
};

export default CandidateDashboard;
