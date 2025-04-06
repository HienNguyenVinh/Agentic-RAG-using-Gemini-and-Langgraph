// src/App.js
import React from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface/ChatInterface';
import Cart from './components/Cart/Cart';

function App() {
  return (
    <div className="App">
      <h1>Book shop</h1>

      <div className="feature-section">
        <h2>Giao diện Chat</h2>
        <ChatInterface />
      </div>

      <div className="feature-section">
        <h2>Giỏ Hàng (User ID: 1)</h2>
        <Cart />
      </div>
    </div>
  );
}

export default App;