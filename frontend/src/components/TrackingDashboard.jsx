import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const TrackingDashboard = () => {
  const [candidateId, setCandidateId] = useState('');  // Default
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Reply form state
  const [replyForm, setReplyForm] = useState({ msgId: null, response: '', show: false });

  const fetchMessages = async (id) => {
    if (!id.trim()) {
      setError('Enter a valid candidate ID. 👤');
      setMessages([]);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${API_BASE}/track/${id.trim()}`);
      setMessages(res.data);
    } catch (err) {
      setError('Failed to fetch: ' + (err.response?.data?.detail || err.message));
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMessages(candidateId);
  }, []);

  const handleIdChange = (e) => {
    const newId = e.target.value;
    setCandidateId(newId);
    fetchMessages(newId);
  };

  const openReplyForm = (msgId) => {
    setReplyForm({ msgId, response: '', show: true });
  };

  const closeReplyForm = () => {
    setReplyForm({ msgId: null, response: '', show: false });
  };

  const saveReply = async () => {
    if (!replyForm.response.trim()) {
      alert('Response required. 💬');
      return;
    }
    const { msgId, response } = replyForm;
    try {
      await axios.post(`${API_BASE}/update-response`, { msg_id: msgId, response });
      alert('Updated as replied! ✅');
      closeReplyForm();
      fetchMessages(candidateId);
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: 0 }}>
      <h2 style={{ color: '#495057', marginBottom: 20 }}>📊 Candidate Message Tracking</h2>
      <p style={{ color: '#6c757d', marginBottom: 20 }}>Enter candidate ID to view messages and mark replies. Tracks full lifecycle.</p>

      {/* ID Input */}
      <div style={{ 
        backgroundColor: '#fff', 
        padding: 20, 
        borderRadius: 8, 
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        border: '1px solid #e9ecef',
        marginBottom: 20
      }}>
        <label style={{ display: 'block', marginBottom: 10, fontWeight: 'bold' }}>Candidate ID:</label>
        <input
          type="text"
          placeholder="e.g., carloschaparrosaenz"
          value={candidateId}
          onChange={handleIdChange}
          style={{ width: '100%', padding: 12, border: '1px solid #dee2e6', borderRadius: 6, fontSize: '14px' }}
        />
      </div>

      {loading && <p style={{ color: '#007bff', textAlign: 'center', padding: 20 }}>Loading... ⏳</p>}
      {error && <p style={{ color: '#dc3545', marginBottom: 20, padding: 10, backgroundColor: '#f8d7da', borderRadius: 6, border: '1px solid #f5c6cb' }}>{error}</p>}
      
      {messages.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#6c757d' }}>
          <p>No messages for ID: {candidateId} 📭</p>
          <p>Generate and accept one first via Message Generator.</p>
        </div>
      ) : (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: 20, 
          borderRadius: 8, 
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
          border: '1px solid #e9ecef'
        }}>
          <h3 style={{ color: '#495057', marginBottom: 15 }}>Messages for {candidateId} ({messages.length}) 📋</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>ID</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Status</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Message Preview</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Sent</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Response</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Replied</th>
                  <th style={{ padding: 12, textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {messages.map((msg, idx) => (
                  <React.Fragment key={idx}>
                    <tr style={{ borderBottom: '1px solid #dee2e6' }}>
                      <td style={{ padding: 12 }}>{msg.id}</td>
                      <td style={{ padding: 12, color: msg.status === 'replied' ? '#28a745' : '#007bff' }}>{msg.status || 'N/A'}</td>
                      <td style={{ padding: 12 }}>{(msg.message || '').substring(0, 50)}...</td>
                      <td style={{ padding: 12 }}>{msg.sent_date || 'N/A'}</td>
                      <td style={{ padding: 12, maxWidth: 150 }}>{msg.response ? msg.response.substring(0, 30) + '...' : 'N/A'}</td>
                      <td style={{ padding: 12 }}>{msg.response_date || 'N/A'}</td>
                      <td style={{ padding: 12 }}>
                        {msg.status !== 'replied' && (
                          <button 
                            onClick={() => openReplyForm(msg.id)} 
                            style={{ padding: '6px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: '12px' }}
                          >
                            Reply 💬
                          </button>
                        )}
                      </td>
                    </tr>
                    {replyForm.show && replyForm.msgId === msg.id && (
                      <tr>
                        <td colSpan="7" style={{ backgroundColor: '#f8f9fa', padding: 20 }}>
                          <h4 style={{ marginBottom: 10 }}>Add Reply (Msg {msg.id})</h4>
                          <textarea
                            value={replyForm.response}
                            onChange={(e) => setReplyForm({ ...replyForm, response: e.target.value })}
                            placeholder="Candidate's response..."
                            style={{ width: '100%', height: 80, padding: 12, border: '1px solid #dee2e6', borderRadius: 6, marginBottom: 10 }}
                          />
                          <button 
                            onClick={saveReply} 
                            style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: 6, marginRight: 10, cursor: 'pointer' }}
                          >
                            Save Reply ✅
                          </button>
                          <button 
                            onClick={closeReplyForm} 
                            style={{ padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer' }}
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
        </div>
      )}
    </div>
  );
};

export default TrackingDashboard;
