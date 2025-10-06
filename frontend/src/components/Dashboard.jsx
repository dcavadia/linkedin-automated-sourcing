import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({});
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [metricsRes, interactionsRes] = await Promise.all([
          axios.get(`${API_BASE}/metrics`),
          axios.get(`${API_BASE}/interactions`)
        ]);
        setMetrics(metricsRes.data);
        setInteractions(interactionsRes.data.slice(0, 10));  // Recent 10
      } catch (err) {
        setError('Failed to load dashboard: ' + (err.response?.data?.detail || err.message));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExport = async () => {
    try {
      const res = await axios.get(`${API_BASE}/export-report`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      alert('Report exported! 📊');
    } catch (err) {
      alert('Export failed: ' + err.message);
    }
  };

  if (loading) return <p style={{ textAlign: 'center', padding: 40, color: '#007bff' }}>Loading dashboard... 📈</p>;
  if (error) return <p style={{ color: '#dc3545', textAlign: 'center', padding: 40 }}>{error}</p>;

  return (
    <div style={{ maxWidth: 1000, margin: 0 }}>
      <h2 style={{ color: '#495057', marginBottom: 20 }}>📈 Candidate Dashboard</h2>
      <p style={{ color: '#6c757d', marginBottom: 20 }}>Overview of outreach effectiveness and recent activity.</p>

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20, marginBottom: 30 }}>
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#6c757d', marginBottom: 10 }}>Total Sent</h3>
          <p style={{ fontSize: '2em', color: '#007bff', margin: 0 }}>{metrics.total_messages_sent || 0} 📤</p>
        </div>
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#6c757d', marginBottom: 10 }}>Replies</h3>
          <p style={{ fontSize: '2em', color: '#28a745', margin: 0 }}>{metrics.total_replies || 0} 💬</p>
        </div>
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#6c757d', marginBottom: 10 }}>Reply Rate</h3>
          <p style={{ fontSize: '2em', color: '#17a2b8', margin: 0 }}>{metrics.reply_rate_percent || 0}% 📈</p>
        </div>
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#6c757d', marginBottom: 10 }}>Avg Reply Time</h3>
          <p style={{ fontSize: '2em', color: '#ffc107', margin: 0 }}>{(metrics.avg_response_time_days || 0).toFixed(1)} days ⏱️</p>
        </div>
      </div>

      {/* Export Button */}
      <button 
        onClick={handleExport}
        style={{ 
          padding: '12px 24px', 
          backgroundColor: '#28a745', 
          color: 'white', 
          border: 'none', 
          borderRadius: 6, 
          cursor: 'pointer',
          fontSize: '16px',
          marginBottom: 20
        }}
      >
        Export Report 📊 (CSV)
      </button>

      {/* Recent Interactions Table */}
      <div style={{ 
        backgroundColor: '#fff', 
        padding: 20, 
        borderRadius: 8, 
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        border: '1px solid #e9ecef'
      }}>
        <h3 style={{ color: '#495057', marginBottom: 15 }}>Recent Interactions (Top 10) 📋</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Candidate</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Sent</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Response</th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((int, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: 12 }}>{int.candidate_name || 'N/A'}</td>
                  <td style={{ padding: 12, color: int.status === 'replied' ? '#28a745' : '#007bff' }}>{int.status}</td>
                  <td style={{ padding: 12 }}>{int.sent_date || 'N/A'}</td>
                  <td style={{ padding: 12 }}>{int.response ? 'Yes 💬' : 'No'}</td>
                </tr>
              ))}
              {interactions.length === 0 && (
                <tr>
                  <td colSpan="4" style={{ padding: 40, textAlign: 'center', color: '#6c757d' }}>No interactions yet. Start outreach! 🚀</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
