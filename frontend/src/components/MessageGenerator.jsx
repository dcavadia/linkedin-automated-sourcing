import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';
const DEFAULT_ROLE_DESC = "AI Engineer role at our innovative startup, focusing on ML pipelines and computer vision.";
const DEFAULT_CTA = "Please reply if interested in discussing this opportunity further.";

const MessageGenerator = () => {
  const [candidates, setCandidates] = useState([]);  // From /candidates
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [msgId, setMsgId] = useState(null);  // Fixed: Store message ID from /generate response
  const [roleDesc, setRoleDesc] = useState(DEFAULT_ROLE_DESC);
  const [cta, setCta] = useState(DEFAULT_CTA);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch candidates on load
  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        const res = await axios.get(`${API_BASE}/candidates`);
        setCandidates(res.data || []);
      } catch (err) {
        setError('Failed to load candidates: ' + (err.response?.data?.detail || err.message));
      }
    };
    fetchCandidates();
  }, []);

  const handleGenerate = async () => {
    if (!selectedCandidate) {
      alert('Select a candidate first. 👤');
      return;
    }
    setGenLoading(true);
    setError('');
    try {
      const postData = {
        id: selectedCandidate.linkedin_id || selectedCandidate.id,
        name: selectedCandidate.name,
        experience: `AI Engineer based on skills: ${selectedCandidate.skills}`,
        current_company: selectedCandidate.current_company || 'N/A',
        role_desc: roleDesc,
        cta: cta
      };
      const res = await axios.post(`${API_BASE}/generate`, postData);
      setMessage(res.data.message);
      setMsgId(res.data.id);  // Fixed: Capture msg_id (int, e.g., 23) from response
      alert(`Message generated for ${selectedCandidate.name}! Review and accept below. ✉️`);
    } catch (err) {
      setError('Error generating: ' + (err.response?.data?.detail || err.message));
    } finally {
      setGenLoading(false);
    }
  };

  const handleCandidateSelect = (candidate) => {
    setSelectedCandidate(candidate);
    setRoleDesc(DEFAULT_ROLE_DESC);
    setCta(DEFAULT_CTA);
    setMessage('');
    setMsgId(null);  // Fixed: Reset msgId on new selection
    setError('');
  };

  const acceptMessage = async () => {
    if (!msgId) {  // Fixed: Check for msgId
      alert('Generate a message first! No message ID available. 🔄');
      return;
    }
    if (!message) return;
    try {
      const res = await axios.post(`${API_BASE}/accept-message/${msgId}`);  // Fixed: Use msgId (int) in URL
      if (res.data.updated) {
        alert('Message marked as sent! 📤');
        setMessage('');  // Clear for next
        setMsgId(null);  // Fixed: Reset after accept
        setRoleDesc(DEFAULT_ROLE_DESC);
        setCta(DEFAULT_CTA);
      } else {
        alert('No message found to update. 😅');
      }
    } catch (err) {
      alert('Error accepting: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: 0 }}>
      <h2 style={{ color: '#495057', marginBottom: 20 }}>✉️ Message Generator</h2>
      <p style={{ color: '#6c757d', marginBottom: 20 }}>Select a candidate from DB, customize role/CTA, generate personalized LinkedIn messages.</p>

      {/* Candidates List */}
      <div style={{ 
        backgroundColor: '#fff', 
        padding: 20, 
        borderRadius: 8, 
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
        border: '1px solid #e9ecef',
        marginBottom: 20
      }}>
        <h3 style={{ color: '#495057', marginBottom: 15 }}>Available Candidates ({candidates.length}) 👥</h3>
        {candidates.length === 0 ? (
          <p style={{ color: '#6c757d' }}>No candidates yet. Search first! 🔍</p>
        ) : (
          <div style={{ maxHeight: 200, overflowY: 'auto' }}>
            {candidates.map((cand, idx) => (
              <button
                key={idx}
                onClick={() => handleCandidateSelect(cand)}
                style={{
                  display: 'block',
                  width: '100%',
                  padding: 12,
                  marginBottom: 8,
                  background: selectedCandidate?.linkedin_id === cand.linkedin_id ? '#e3f2fd' : '#f8f9fa',
                  border: '1px solid #dee2e6',
                  borderRadius: 6,
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                {cand.name} – {cand.skills} (Score: {cand.relevance_score})
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedCandidate && (
        <>
          <p style={{ color: '#6c757d', marginBottom: 20 }}>
            Selected: {selectedCandidate.name} (ID: {selectedCandidate.linkedin_id}) | Skills: {selectedCandidate.skills}
          </p>

          {/* Form */}
          <div style={{ 
            backgroundColor: '#fff', 
            padding: 20, 
            borderRadius: 8, 
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            border: '1px solid #e9ecef'
          }}>
            <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>Role Description:</label>
            <textarea
              value={roleDesc}
              onChange={(e) => setRoleDesc(e.target.value)}
              placeholder="e.g., AI Engineer focusing on computer vision..."
              style={{ width: '100%', height: 80, padding: 12, border: '1px solid #dee2e6', borderRadius: 6, marginBottom: 15, fontSize: '14px' }}
            />
            
            <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>Call to Action:</label>
            <input
              type="text"
              value={cta}
              onChange={(e) => setCta(e.target.value)}
              placeholder="e.g., Reply to schedule a call"
              style={{ width: '100%', padding: 12, border: '1px solid #dee2e6', borderRadius: 6, marginBottom: 15, fontSize: '14px' }}
            />
            
            <button 
              onClick={handleGenerate} 
              disabled={genLoading}
              style={{ 
                padding: '12px 24px', 
                backgroundColor: genLoading ? '#6c757d' : '#28a745', 
                color: 'white', 
                border: 'none', 
                borderRadius: 6, 
                cursor: genLoading ? 'not-allowed' : 'pointer',
                marginRight: 10,
                fontSize: '16px'
              }}
            >
              {genLoading ? 'Generating...' : 'Generate Message ✉️'}
            </button>
            
            {message && msgId && (  // Fixed: Show accept only if msgId exists
              <>
                <button 
                  onClick={acceptMessage}
                  style={{ 
                    padding: '12px 24px', 
                    backgroundColor: '#007bff', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: 6, 
                    cursor: 'pointer',
                    fontSize: '16px'
                  }}
                >
                  Accept & Send 📤
                </button>
                <div style={{ marginTop: 20, padding: 15, backgroundColor: '#e3f2fd', borderRadius: 6, border: '1px solid #bee5eb' }}>
                  <h4>Generated Message (Msg ID: {msgId}):</h4>  {/* Fixed: Show msgId in preview */}
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontSize: '14px' }}>{message}</pre>
                </div>
              </>
            )}
          </div>
        </>
      )}

      {error && <p style={{ color: '#dc3545', marginTop: 20, padding: 10, backgroundColor: '#f8d7da', borderRadius: 6, border: '1px solid #f5c6cb' }}>{error}</p>}
    </div>
  );
};

export default MessageGenerator;
