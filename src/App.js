import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import Main from './components/Main';
import Footer from './components/Footer';

function App() {
  const [nodes, setNodes] = useState([]);

  const onAddNode = (type, label) => {
    const newNode = {
      id: Date.now(),
      type,
      label,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 }
    };
    setNodes(prevNodes => [...prevNodes, newNode]);
  };

  return (
    <div className="app-container">
      <Header onAddNode={onAddNode} />
      <Main nodes={nodes} />
      <Footer />
    </div>
  );
}

export default App;