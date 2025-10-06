import React, { useState } from 'react';
import SearchModule from './components/SearchModule';
import MessageGenerator from './components/MessageGenerator';
import TrackingDashboard from './components/TrackingDashboard';
import Dashboard from './components/Dashboard';

const App = () => {
  const [activeModule, setActiveModule] = useState('search');  // Default: Search

  const renderModule = () => {
    switch (activeModule) {
      case 'search': return <SearchModule />;
      case 'generator': return <MessageGenerator />;
      case 'tracking': return <TrackingDashboard />;
      case 'dashboard': return <Dashboard />;
      default: return <SearchModule />;
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      minHeight: '100vh', 
      fontFamily: 'system-ui, sans-serif', 
      backgroundColor: '#f8f9fa',
      color: '#333'
    }}>
      {/* Left Sidebar */}
      <nav style={{ 
        width: '200px', 
        backgroundColor: '#fff', 
        borderRight: '1px solid #e9ecef',
        padding: '20px 0',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <h2 style={{ padding: '0 20px 20px', fontSize: '1.2em', color: '#495057' }}>Recruiter App</h2>
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          <li>
            <button
              onClick={() => setActiveModule('search')}
              style={{
                width: '100%',
                padding: '12px 20px',
                border: 'none',
                background: activeModule === 'search' ? '#007bff' : 'transparent',
                color: activeModule === 'search' ? '#fff' : '#333',
                textAlign: 'left',
                fontSize: '1em',
                cursor: 'pointer',
                transition: 'background 0.2s',
                borderRight: activeModule === 'search' ? '3px solid #007bff' : 'none'
              }}
            >
              🔍 LinkedIn Search
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveModule('generator')}
              style={{
                width: '100%',
                padding: '12px 20px',
                border: 'none',
                background: activeModule === 'generator' ? '#007bff' : 'transparent',
                color: activeModule === 'generator' ? '#fff' : '#333',
                textAlign: 'left',
                fontSize: '1em',
                cursor: 'pointer',
                transition: 'background 0.2s',
                borderRight: activeModule === 'generator' ? '3px solid #007bff' : 'none'
              }}
            >
              ✉️ Message Generator
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveModule('tracking')}
              style={{
                width: '100%',
                padding: '12px 20px',
                border: 'none',
                background: activeModule === 'tracking' ? '#007bff' : 'transparent',
                color: activeModule === 'tracking' ? '#fff' : '#333',
                textAlign: 'left',
                fontSize: '1em',
                cursor: 'pointer',
                transition: 'background 0.2s',
                borderRight: activeModule === 'tracking' ? '3px solid #007bff' : 'none'
              }}
            >
              📊 Message Tracking
            </button>
          </li>
          <li>
            <button
              onClick={() => setActiveModule('dashboard')}
              style={{
                width: '100%',
                padding: '12px 20px',
                border: 'none',
                background: activeModule === 'dashboard' ? '#007bff' : 'transparent',
                color: activeModule === 'dashboard' ? '#fff' : '#333',
                textAlign: 'left',
                fontSize: '1em',
                cursor: 'pointer',
                transition: 'background 0.2s',
                borderRight: activeModule === 'dashboard' ? '3px solid #007bff' : 'none'
              }}
            >
              📈 Candidate Dashboard
            </button>
          </li>
        </ul>
      </nav>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        {renderModule()}
      </main>
    </div>
  );
};

export default App;
