import React from 'react';
import MessageGenerator from './components/MessageGenerator';
import TrackingDashboard from './components/TrackingDashboard';
import CandidateDashboard from './components/CandidateDashboard';  // New import

function App() {
  return (
    <div className="App" style={{ maxWidth: 800, margin: 'auto', padding: 20 }}>
      <h1>LinkedIn Message Generator & Management</h1>
      <MessageGenerator />  {/* Module 2: Generate & Save */}
      <hr style={{ margin: '20px 0' }} />
      <TrackingDashboard />  {/* Module 2: Track Individual */}
      <hr style={{ margin: '20px 0' }} />
      <CandidateDashboard />  {/* Module 3 Step 2: Overview Dashboard */}
    </div>
  );
}

export default App;
