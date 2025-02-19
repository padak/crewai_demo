import React, { useState, useEffect } from 'react';
import './App.css';

const AGENT_CONFIG = {
  'Research Agent': {
    role: 'Research Analyst',
    description: 'Gathers and analyzes information on the given topic',
    dependencies: [],
    status: 'idle'
  },
  'Writer Agent': {
    role: 'Content Writer',
    description: 'Creates engaging content based on research',
    dependencies: ['Research Agent'],
    status: 'idle'
  },
  'Editor Agent': {
    role: 'Content Editor',
    description: 'Reviews and optimizes the content',
    dependencies: ['Writer Agent'],
    status: 'idle'
  }
};

function App() {
  const [messages, setMessages] = useState([]);
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [isRunning, setIsRunning] = useState(false);
  const [topic, setTopic] = useState('');
  const [agents, setAgents] = useState(AGENT_CONFIG);

  // Group messages by agent and phase
  const groupedMessages = messages.reduce((acc, msg) => {
    const key = msg.agent;
    if (!acc[key]) {
      acc[key] = [];
    }
    // Only add message if it's not a duplicate
    const isDuplicate = acc[key].some(m => 
      m.task === msg.task && 
      m.output === msg.output &&
      Math.abs(new Date(m.timestamp) - new Date(msg.timestamp)) < 1000
    );
    if (!isDuplicate) {
      acc[key].push(msg);
    }
    return acc;
  }, {});

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://161.35.192.142:8000/ws');
      
      ws.onopen = () => {
        console.log('Connected to WebSocket');
        setConnectionStatus('Connected to monitoring server');
        setSocket(ws);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        // Skip acknowledgment messages
        if (data.type === 'ack') return;
        
        // Update agent status if it's an agent message
        if (data.type === 'status' && data.agent in AGENT_CONFIG) {
          setAgents(prev => ({
            ...prev,
            [data.agent]: {
              ...prev[data.agent],
              status: data.task
            }
          }));
          setIsRunning(true);
        }
        
        // Handle completion
        if (data.task === 'Completed' && data.agent === 'Editor Agent') {
          setIsRunning(false);
        }
        
        // Add message to log
        setMessages(prev => [...prev, data]);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('Error connecting to server');
        setIsRunning(false);
        setTimeout(connectWebSocket, 5000);
      };

      ws.onclose = () => {
        console.log('Disconnected from WebSocket');
        setConnectionStatus('Disconnected from server');
        setIsRunning(false);
        setTimeout(connectWebSocket, 5000);
      };

      return () => {
        ws.close();
      };
    };

    connectWebSocket();
  }, []);

  const handleStartCrewAI = async () => {
    if (!topic.trim()) {
      alert('Please enter a topic');
      return;
    }

    try {
      setIsRunning(true);
      setMessages([]);
      const response = await fetch('http://161.35.192.142:8000/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error('Failed to start CrewAI');
      }
    } catch (error) {
      console.error('Error starting CrewAI:', error);
      setIsRunning(false);
      alert('Failed to start CrewAI. Please try again.');
    }
  };

  const handleClearLogs = () => {
    setMessages([]);
    setAgents(AGENT_CONFIG);
  };

  // Render a single message group
  const renderMessageGroup = (agentName, messages) => {
    const latestMessage = messages[messages.length - 1];
    const isSystem = agentName === 'System';
    
    return (
      <div key={agentName} className={`message-group ${isSystem ? 'system' : 'agent'}`}>
        <div className="message-group-header">
          <span className="agent-name">{agentName}</span>
          <span className="timestamp">{new Date(latestMessage.timestamp).toLocaleTimeString()}</span>
        </div>
        <div className="message-group-content">
          {messages.map((msg, idx) => (
            <div key={idx} className="message-item">
              <span className="task-label">{msg.task}</span>
              <span className="message-text">{msg.output}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>CrewAI Agent Monitor</h1>
        <div className={`connection-status ${connectionStatus.includes('Connected') ? 'connected' : 'disconnected'}`}>
          {connectionStatus}
        </div>
      </header>
      <div className="control-panel">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter topic for content creation..."
          disabled={isRunning}
          className="topic-input"
        />
        <div className="button-group">
          <button
            onClick={handleStartCrewAI}
            disabled={isRunning || !topic.trim()}
            className={`control-button ${isRunning ? 'running' : ''}`}
          >
            {isRunning ? 'Running...' : 'Start CrewAI'}
          </button>
          <button
            onClick={handleClearLogs}
            disabled={isRunning || messages.length === 0}
            className="control-button clear"
          >
            Clear Logs
          </button>
        </div>
      </div>
      <div className="dashboard">
        <div className="agent-overview">
          <h2>Agent Overview</h2>
          <div className="agent-workflow">
            {Object.entries(agents).map(([name, agent], index) => (
              <div key={name} className={`agent-node ${agent.status !== 'idle' ? 'active' : ''}`}>
                <div className="agent-info">
                  <h3>{name}</h3>
                  <p className="agent-role">{agent.role}</p>
                  <p className="agent-description">{agent.description}</p>
                  <div className={`agent-status ${agent.status !== 'idle' ? 'active' : ''}`}>
                    {agent.status === 'idle' ? 'Waiting' : agent.status}
                  </div>
                </div>
                {index < Object.entries(agents).length - 1 && (
                  <div className="workflow-arrow">→</div>
                )}
              </div>
            ))}
          </div>
        </div>
        <main>
          <div id="message-container" className="agent-activities">
            {messages.length === 0 ? (
              <div className="no-activity">
                <p>Waiting for agent activities...</p>
                <p className="hint">Enter a topic and click Start CrewAI to begin</p>
              </div>
            ) : (
              <div className="message-groups">
                {Object.entries(groupedMessages).map(([agentName, messages]) => 
                  renderMessageGroup(agentName, messages)
                )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App; 