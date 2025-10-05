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
      setMessages(res.data || []);  // Ensure array even if null/undefined
    } catch (err) {
      alert('Error fetching messages: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateResponse = async (msgId) => {
    const responseText = prompt('Enter response for this message:');
    if (!responseText) return;
    try {
      await axios.post(`${API_BASE}/update-response`, { msg_id: msgId, response: responseText });
      await fetchMessages(); // refresh list
    } catch (err) {
      alert('Error updating response: ' + err.message);
    }
  };

  return (
    <div>
      <h2>Candidate Message Tracking</h2>
      <input
        type="text"
        placeholder="Enter Candidate ID"
        value={candidateId}
        onChange={(e) => setCandidateId(e.target.value)}
      />
      <button onClick={fetchMessages} disabled={loading || !candidateId}>
        {loading ? 'Loading...' : 'Load Messages'}
      </button>

      {messages.length > 0 && (
        <table border="1" cellPadding="5" style={{ marginTop: 20, width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Message Preview</th>
              <th>Sent Date</th>
              <th>Response</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {messages.map((msg) => (
              <tr key={msg.id}>
                <td>{msg.id}</td>
                <td>
                  {msg.message ? (msg.message.length > 50 ? msg.message.substring(0, 50) + '...' : msg.message) : 'N/A'}
                </td>
                <td>{msg.sent_date || 'N/A'}</td>
                <td>{msg.response || 'None'}</td>
                <td>{msg.status || 'N/A'}</td>
                <td>
                  <button onClick={() => handleUpdateResponse(msg.id)}>Log Response</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {messages.length === 0 && !loading && candidateId && (
        <p>No messages found for this candidate.</p>
      )}
    </div>
  );
};

export default TrackingDashboard;
