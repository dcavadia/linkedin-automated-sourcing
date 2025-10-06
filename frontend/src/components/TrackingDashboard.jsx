import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const TrackingDashboard = () => {
  const [candidateId, setCandidateId] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchMessages = async () => {
    if (!candidateId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/track/${candidateId}`);
      // Format dates if ISO strings
      const formatted = (res.data || []).map(msg => ({
        ...msg,
        sent_date: msg.sent_date ? new Date(msg.sent_date).toLocaleString() : 'Not Sent Yet',
        response_date: msg.response_date ? new Date(msg.response_date).toLocaleString() : 'N/A'
      }));
      setMessages(formatted);
    } catch (err) {
      alert('Error fetching messages: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateResponse = async (msgId) => {
    const responseText = prompt('Enter candidate response for this message:');
    if (!responseText) return;
    try {
      await axios.post(`${API_BASE}/update-response`, { msg_id: msgId, response: responseText });
      await fetchMessages(); // refresh
      alert('Response logged and status updated to replied!');
    } catch (err) {
      alert('Error updating response: ' + err.message);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h2>Candidate Message Tracking</h2>
      <input
        type="text"
        placeholder="Enter Candidate ID (e.g., carlosalfonsochaparosaenz)"
        value={candidateId}
        onChange={(e) => setCandidateId(e.target.value)}
        style={{ padding: 8, width: '300px', border: '1px solid #ccc', borderRadius: 4, marginRight: 10 }}
      />
      <button onClick={fetchMessages} disabled={loading || !candidateId} style={{ padding: '8px 16px', backgroundColor: (loading || !candidateId) ? '#6c757d' : '#007bff', color: 'white', border: 'none', borderRadius: 4 }}>
        {loading ? 'Loading...' : 'Load Messages'}
      </button>

      {messages.length > 0 && (
        <table border="1" cellPadding="5" style={{ marginTop: 20, width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f0f0f0' }}>
              <th>ID</th>
              <th>Message Preview</th>
              <th>Status</th>
              <th>Sent Date</th>
              <th>Response</th>
              <th>Response Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {messages.map((msg) => (
              <tr key={msg.id}>
                <td>{msg.id}</td>
                <td>{msg.message ? (msg.message.length > 50 ? msg.message.substring(0, 50) + '...' : msg.message) : 'N/A'}</td>
                <td><strong>{msg.status || 'generated'}</strong></td>  {/* Highlight status */}
                <td>{msg.sent_date}</td>
                <td>{msg.response || 'None'}</td>
                <td>{msg.response_date}</td>
                <td>
                  {msg.status !== 'replied' && (  // Only if not replied
                    <button onClick={() => handleUpdateResponse(msg.id)} style={{ padding: '4px 8px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: 2 }}>
                      Log Response
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {messages.length === 0 && !loading && candidateId && (
        <p style={{ marginTop: 20 }}>No messages found for this candidate (ID: {candidateId}). Generate and accept one first via Search or Generator module.</p>
      )}
    </div>
  );
};

export default TrackingDashboard;
