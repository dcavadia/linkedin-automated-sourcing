import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const TrackingDashboard = () => {
  const [candidateId, setCandidateId] = useState('carloschaparrosaenz');  // Default to your example; user can change
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // New: Reply form state (per message)
  const [replyForm, setReplyForm] = useState({ msgId: null, response: '', show: false });

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

  // New: Open reply form for specific message
  const openReplyForm = (msgId) => {
    setReplyForm({ msgId, response: '', show: true });
  };

  // New: Close reply form
  const closeReplyForm = () => {
    setReplyForm({ msgId: null, response: '', show: false });
  };

  // New: Save reply (POST to /update-response)
  const saveReply = async () => {
    if (!replyForm.response.trim()) {
      alert('Response text is required.');
      return;
    }
    const { msgId, response } = replyForm;
    try {
      await axios.post(`${API_BASE}/update-response`, { msg_id: msgId, response });
      alert('Response updated and marked as replied!');
      closeReplyForm();
      fetchMessages(candidateId);  // Refetch to show updates
    } catch (err) {
      alert('Error updating response: ' + (err.response?.data?.detail || err.message));
    }
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
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {messages.map((msg, idx) => (
                <React.Fragment key={idx}>
                  <tr>
                    <td>{msg.id}</td>
                    <td>{msg.status || 'N/A'}</td>
                    <td>{(msg.message || '').substring(0, 100)}...</td>
                    <td>{msg.sent_date || 'N/A'}</td>
                    <td>{msg.response ? msg.response.substring(0, 50) + '...' : 'N/A'}</td>
                    <td>{msg.response_date || 'N/A'}</td>
                    <td>
                      {msg.status !== 'replied' && (
                        <button 
                          onClick={() => openReplyForm(msg.id)} 
                          style={{ padding: '4px 8px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: 2, cursor: 'pointer' }}
                        >
                          Mark as Replied
                        </button>
                      )}
                    </td>
                  </tr>
                  {/* New: Inline Reply Form (shows below row if open for this msgId) */}
                  {replyForm.show && replyForm.msgId === msg.id && (
                    <tr>
                      <td colSpan="7" style={{ backgroundColor: '#f9f9f9' }}>
                        <h4>Mark as Replied (Message {msg.id})</h4>
                        <textarea
                          value={replyForm.response}
                          onChange={(e) => setReplyForm({ ...replyForm, response: e.target.value })}
                          placeholder="Enter candidate's response (e.g., 'Interested, when can we chat?')"
                          style={{ width: '100%', height: 80, padding: 8, border: '1px solid #ccc', borderRadius: 4, marginBottom: 10 }}
                        />
                        <button 
                          onClick={saveReply} 
                          style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: 4, marginRight: 10 }}
                        >
                          Save Reply
                        </button>
                        <button 
                          onClick={closeReplyForm} 
                          style={{ padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: 4 }}
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TrackingDashboard;
