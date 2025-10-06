import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';
const DEFAULT_ROLE_DESC = "AI Engineer role at our innovative startup, focusing on ML pipelines and computer vision.";
const DEFAULT_CTA = "Please reply if interested in discussing this opportunity further.";

const MessageGenerator = () => {
  const [candidate, setCandidate] = useState({ id: '', name: '', experience: 'impressive AI engineering background' });  // No company
  const [roleDesc, setRoleDesc] = useState(DEFAULT_ROLE_DESC);
  const [cta, setCta] = useState(DEFAULT_CTA);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showAcceptReject, setShowAcceptReject] = useState(false);
  const [msgId, setMsgId] = useState(null);

  const handleInputChange = (e) => {
    setCandidate({ ...candidate, [e.target.name]: e.target.value });
  };

  const generateMessage = async () => {
    if (!candidate.id || !candidate.name) {
      alert('ID and Name required.');
      return;
    }
    setLoading(true);
    try {
      const postData = {
        ...candidate,
        role_desc: roleDesc,
        cta: cta
      };
      const res = await axios.post(`${API_BASE}/generate`, postData);
      setMessage(res.data.message);
      setMsgId(res.data.id);
      setShowAcceptReject(true);
      alert('Message generated! Review and accept to send.');
    } catch (err) {
      alert('Error generating message: ' + err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const acceptMessage = async () => {
    try {
      const res = await axios.post(`${API_BASE}/accept-message/${msgId}`);
      if (res.data.updated) {
        alert('Message accepted and marked as sent!');
        setShowAcceptReject(false);
      }
    } catch (err) {
      alert('Error accepting message: ' + err.message);
    }
  };

  const rejectMessage = () => {
    setMessage('');
    setShowAcceptReject(false);
    setMsgId(null);
    alert('Message rejected. Regenerate as needed.');
  };

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: 20 }}>
      <h2>Message Generator</h2>
      <input name="id" placeholder="Candidate ID (linkedin_id)" value={candidate.id} onChange={handleInputChange} style={{ display: 'block', marginBottom: 10, padding: 8, width: '100%', border: '1px solid #ccc', borderRadius: 4 }} />
      <input name="name" placeholder="Name" value={candidate.name} onChange={handleInputChange} style={{ display: 'block', marginBottom: 10, padding: 8, width: '100%', border: '1px solid #ccc', borderRadius: 4 }} />
      <input name="experience" placeholder="Experience (e.g., impressive AI background)" value={candidate.experience} onChange={handleInputChange} style={{ display: 'block', marginBottom: 10, padding: 8, width: '100%', border: '1px solid #ccc', borderRadius: 4 }} />
      {/* No company input */}
      <label>Brief Role Description:</label>
      <textarea value={roleDesc} onChange={(e) => setRoleDesc(e.target.value)} placeholder="e.g., AI Engineer focusing on computer vision" style={{ display: 'block', marginBottom: 10, padding: 8, width: '100%', height: 80, border: '1px solid #ccc', borderRadius: 4 }} />
      <label>Clear Call to Action:</label>
      <input type="text" value={cta} onChange={(e) => setCta(e.target.value)} placeholder="e.g., Reply to schedule a call" style={{ display: 'block', marginBottom: 10, padding: 8, width: '100%', border: '1px solid #ccc', borderRadius: 4 }} />
      <button onClick={generateMessage} disabled={loading || showAcceptReject} style={{ padding: '10px 20px', backgroundColor: (loading || showAcceptReject) ? '#6c757d' : '#28a745', color: 'white', border: 'none', borderRadius: 4 }}>
        {loading ? 'Generating...' : 'Generate Message'}
      </button>
      {showAcceptReject && message && (
        <div style={{ marginTop: 20, padding: 15, backgroundColor: '#e8f4fd', borderRadius: 4 }}>
          <h4>Review Generated Message:</h4>
          <pre style={{ whiteSpace: 'pre-wrap', margin: 0, border: '1px solid #ddd', padding: 10, backgroundColor: 'white' }}>{message}</pre>
          <button onClick={acceptMessage} style={{ padding: '8px 16px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: 4, marginRight: 10, marginTop: 10 }}>
            Accept & Send
          </button>
          <button onClick={rejectMessage} style={{ padding: '8px 16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: 4, marginTop: 10 }}>
            Reject & Regenerate
          </button>
        </div>
      )}
    </div>
  );
};

export default MessageGenerator;
