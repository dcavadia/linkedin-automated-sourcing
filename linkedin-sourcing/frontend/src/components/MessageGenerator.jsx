import React, { useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const MessageGenerator = () => {
  const [candidate, setCandidate] = useState({ id: '', name: '', experience: '', current_company: '' });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    setCandidate({ ...candidate, [e.target.name]: e.target.value });
  };

  const generateMessage = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/generate`, candidate);
      setMessage(res.data.message);
      alert('Message generated!');
    } catch (err) {
      alert('Error generating message: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <div>
      <input name="id" placeholder="Candidate ID" value={candidate.id} onChange={handleInputChange} />
      <input name="name" placeholder="Name" value={candidate.name} onChange={handleInputChange} />
      <input name="experience" placeholder="Experience" value={candidate.experience} onChange={handleInputChange} />
      <input name="current_company" placeholder="Current Company" value={candidate.current_company} onChange={handleInputChange} />
      <button onClick={generateMessage} disabled={loading}>Generate Message</button>
      {message && <pre style={{ marginTop: 20, whiteSpace: 'pre-wrap' }}>{message}</pre>}
    </div>
  );
};

export default MessageGenerator;
