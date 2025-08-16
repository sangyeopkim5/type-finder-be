import React, { useState } from 'react';
import './Footer.css';

function Footer() {
  const [messages, setMessages] = useState([
    { text: '피타고라스 정리에 대해 설명해주세요.', sender: 'user', time: '2분 전' },
    { text: '피타고라스 정리는 직각삼각형에서 빗변의 제곱이 다른 두 변의 제곱의 합과 같다는 정리입니다.', sender: 'assistant', time: '1분 전' }
  ]);
  const [inputValue, setInputValue] = useState('');

  const handleQuestionSubmit = (e) => {
    if (e.key === 'Enter' && inputValue.trim() !== '') {
      const newMessages = [...messages, { text: inputValue, sender: 'user', time: '방금 전' }];
      setMessages(newMessages);
      setInputValue('');
      
      // Simulate AI response after 1 second
      setTimeout(() => {
        setMessages(prevMessages => [...prevMessages, { text: '답변을 생성 중입니다...', sender: 'assistant', time: '방금 전' }]);
      }, 1000);
    }
  };

  return (
    <div className="right-sidebar">
      {/* Video section can also be made dynamic later */}
      <div className="sidebar-section video-section">
        {/* ... Video section JSX ... */}
      </div>

      <div className="sidebar-section chat-section">
        <div className="section-header">
          {/* ... Chat header JSX ... */}
        </div>
        <div className="chat-content">
          <div className="chat-title">피타고라스 정리의 증명</div>
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.sender}`}>
                <p>{msg.text}</p>
                <span>{msg.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="sidebar-section question-section">
        <div className="question-input-container">
          <input 
            type="text" 
            placeholder="해당 노드에 대한 질문을 입력하세요.." 
            className="question-input"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleQuestionSubmit}
          />
        </div>
      </div>
      
      <button className="collapse-btn">
        {/* Collapse button SVG */}
      </button>
    </div>
  );
}

export default Footer;