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
      setLoading(true);
      setError('');
      try {
        const metricsRes = await axios.get(`${API_BASE}/metrics`);
        setMetrics(metricsRes.data || {});

        const interactionsRes = await axios.get(`${API_BASE}/interactions`);
        setInteractions(interactionsRes.data || []);
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
      link.setAttribute('download', `candidate-report-${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      alert('Report exported! 📊');
    } catch (err) {
      alert('Export failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40, color: '#6c757d' }}>Loading dashboard... ⏳</div>;
  }

  if (error) {
    return <p style={{ color: '#dc3545', textAlign: 'center', padding: 40 }}>{error}</p>;
  }

  return (
    <div style={{ maxWidth: 1200, margin: 0 }}>
      <h2 style={{ color: '#495057', marginBottom: 20 }}>📈 Candidate Dashboard</h2>
      <p style={{ color: '#6c757d', marginBottom: 30 }}>Overview of outreach efforts and recent interactions. Export for full reports.</p>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: 20, 
        marginBottom: 30 
      }}>
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

      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 20 
      }}>
        <h3 style={{ color: '#495057', margin: 0 }}>Recent Interactions (Top 10) 📋</h3>
        <button 
          onClick={handleExport}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: '#28a745', 
            color: 'white', 
            border: 'none', 
            borderRadius: 6, 
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Export Report 📊 CSV
        </button>
      </div>

      {interactions.length === 0 ? (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 40, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          textAlign: 'center',
          color: '#6c757d'
        }}>
          <p>No interactions yet. Send some messages first! ✉️</p>
        </div>
      ) : (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef',
          overflowX: 'auto'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Msg ID</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Candidate ID</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Name</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Sent</th>
                <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Response</th>
              </tr>
            </thead>
            <tbody>
              {interactions.slice(0, 10).map((msg, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: 12 }}>{msg.id || 'N/A'}</td>
                  <td style={{ padding: 12, fontSize: '12px', color: '#6c757d' }}>
                    {msg.candidate_id 
                      ? msg.candidate_id.substring(0, 20) + (msg.candidate_id.length > 20 ? '...' : '') 
                      : 'N/A'
                    }
                  </td>
                  <td style={{ padding: 12, fontWeight: 'bold' }}>{msg.candidate_name || 'Unknown'}</td>
                  <td style={{ 
                    padding: 12, 
                    color: msg.status === 'replied' ? '#28a745' : (msg.status === 'sent' ? '#007bff' : '#6c757d')
                  }}>
                    {msg.status || 'N/A'}
                  </td>
                  <td style={{ padding: 12 }}>
                    {msg.sent_date ? new Date(msg.sent_date).toLocaleDateString() : 'N/A'}
                  </td>
                  <td style={{ padding: 12, maxWidth: 200 }}>
                    {msg.response ? msg.response.substring(0, 50) + '...' : 'No'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
