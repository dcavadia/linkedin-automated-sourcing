import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const TrackingDashboard = () => {
  const [candidateId, setCandidateId] = useState('carloschaparrosaenz');  // Default to your example; user can change
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchMessages = async (id) => {
    if (!id.trim()) {
      setError('Enter a valid candidate ID.');
      setMessages([]);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE}/track/${id.trim()}`);
      setMessages(res.data);  // Expects [] or array of messages
    } catch (err) {
      setError('Failed to fetch tracking data: ' + (err.response?.data?.detail || err.message));
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch on mount with default ID
  useEffect(() => {
    fetchMessages(candidateId);
  }, []);

  const handleIdChange = (e) => {
    const newId = e.target.value;
    setCandidateId(newId);
    fetchMessages(newId);  // Fetch on change for real-time
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>Candidate Message Tracking</h2>
      <p>Enter the exact candidate ID (linkedin_id) used in generation (e.g., from Search results or Generator input).</p>
      
      {/* ID Input */}
      <input
        type="text"
        placeholder="Candidate ID (e.g., carloschaparrosaenz)"
        value={candidateId}
        onChange={handleIdChange}
        style={{ display: 'block', marginBottom: 20, padding: 8, width: '100%', border: '1px solid #ccc', borderRadius: 4 }}
      />
      
      {loading && <p style={{ color: 'blue' }}>Loading messages...</p>}
      {error && <p style={{ color: 'red', marginBottom: 10 }}>{error}</p>}
      
      {/* Messages Table or Empty Message */}
      {messages.length === 0 ? (
        <p>No messages found for this candidate (ID: {candidateId}). Generate and accept one first via Search or Generator module.</p>
      ) : (
        <div>
          <h3>Messages for {candidateId} ({messages.length} found)</h3>
          <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f0f0f0' }}>
                <th>Message ID</th>
                <th>Status</th>
                <th>Message Preview</th>
                <th>Sent Date</th>
                <th>Response</th>
                <th>Response Date</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((msg, idx) => (
                <tr key={idx}>
                  <td>{msg.id}</td>
                  <td>{msg.status || 'N/A'}</td>
                  <td>{(msg.message || '').substring(0, 100)}...</td>
                  <td>{msg.sent_date || 'N/A'}</td>
                  <td>{msg.response || 'N/A'}</td>
                  <td>{msg.response_date || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TrackingDashboard;
