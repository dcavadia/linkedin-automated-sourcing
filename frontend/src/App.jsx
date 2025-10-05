import React from 'react';
import SearchModule from './components/SearchModule';  // Module 1: Search & Populate DB
import MessageGenerator from './components/MessageGenerator';  // Module 2
import TrackingDashboard from './components/TrackingDashboard';  // Module 2
import CandidateDashboard from './components/CandidateDashboard';  // Module 3

function App() {
  return (
    <div className="App" style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h1>LinkedIn Automated Sourcing System</h1>
      <SearchModule />  {/* Module 1: Identify & Save Candidates */}
      <hr style={{ margin: '40px 0' }} />
      <MessageGenerator />  {/* Module 2: Generate Messages (use candidate_id from search) */}
      <hr style={{ margin: '20px 0' }} />
      <TrackingDashboard />  {/* Module 2: Track Responses */}
      <hr style={{ margin: '20px 0' }} />
      <CandidateDashboard />  {/* Module 3: Pipeline Overview (now includes searched candidates) */}
    </div>
  );
}

export default App;
