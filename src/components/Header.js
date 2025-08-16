import React, { useState, useEffect } from 'react';
import './Header.css';

// App.js로부터 onAddNode 함수를 props로 받아옵니다.
function Header({ onAddNode }) {
  // '세트 이름' 편집 상태와 값을 관리하기 위한 state
  const [isEditingName, setIsEditingName] = useState(false);
  const [setName, setSetName] = useState('Untitled');

  // 컴포넌트가 처음 로드될 때 localStorage에서 저장된 이름을 불러옵니다.
  useEffect(() => {
    const savedName = localStorage.getItem('setName');
    if (savedName) {
      setSetName(savedName);
      document.title = `${savedName} - M`;
    }
  }, []); // []는 처음 한 번만 실행하라는 의미입니다.

  // input 값이 변경될 때 setName 상태를 업데이트합니다.
  const handleNameChange = (e) => {
    setSetName(e.target.value);
  };

  // input에서 포커스가 벗어나거나 Enter 키를 누르면 이름을 저장합니다.
  const handleSaveName = () => {
    const finalName = setName.trim() || 'Untitled';
    localStorage.setItem('setName', finalName);
    document.title = `${finalName} - M`;
    setSetName(finalName);
    setIsEditingName(false); // 다시 텍스트 형태로 보이게 합니다.
  };

  // 노드 타입 정보를 배열로 관리하여 쉽게 렌더링합니다.
  const nodeTypes = [
    { type: 'concept', label: '개념 심화 노드', description: '개념 심화, 증명, 연관개념' },
    { type: 'strategy', label: '전략 수립 노드', description: '풀이전략 & 스토리보드' },
    { type: 'visualization', label: '시각화 노드', description: '그래프, 이미지, 3D 도형' },
    { type: 'video', label: '영상화 노드', description: '시각화, 풀이 영상' },
    { type: 'summary', label: '요약 노드', description: '오디오, Text요약' }
  ];

  return (
    // ▼▼▼▼▼ 기존의 모든 UI 코드는 여기에 그대로 있습니다 ▼▼▼▼▼
    <div className="left-sidebar" data-node-id="63:2451">
      <div className="sidebar-content">
        <div className="logo-section">
          <div className="logo">M</div>
          <button className="fold-button">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M21 19.5C21 19.8978 20.842 20.2794 20.5607 20.5607C20.2794 20.842 19.8978 21 19.5 21L4.5 21C4.10218 21 3.72065 20.842 3.43934 20.5607C3.15804 20.2794 3 19.8978 3 19.5L3 4.5C3 4.10218 3.15804 3.72065 3.43934 3.43934C3.72065 3.15804 4.10218 3 4.5 3L19.5 3C19.8978 3 20.2794 3.15804 20.5607 3.43934C20.842 3.72065 21 4.10218 21 4.5L21 19.5Z" stroke="black" strokeWidth="2" strokeLinejoin="round"/>
              <path d="M8 21L8 3M16 14L14 12L16 10M11 21H5M11 3H5" stroke="black" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>

        <div className="section-title">세트이름</div>
        
        {/* 'isEditingName' 상태에 따라 input을 보여주거나 텍스트를 보여줍니다. */}
        {isEditingName ? (
          <div className="set-name-input">
            <input
              type="text"
              value={setName}
              onChange={handleNameChange}
              onBlur={handleSaveName}
              onKeyDown={e => e.key === 'Enter' && handleSaveName()}
              autoFocus
            />
          </div>
        ) : (
          <div className="set-name-display" onClick={() => setIsEditingName(true)}>
            <span className="set-name-text">{setName}</span>
            <div className="set-name-edit-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3H5C4.44772 3 4 3.44772 4 4V7M8 3V7M8 3H11C11.5523 3 12 3.44772 12 4V7M8 7H4M8 7H12M8 7V11M4 7V11M12 7V11M8 11H4M8 11H12" stroke="currentColor" strokeWidth="1.5"/></svg>
            </div>
          </div>
        )}

        <div className="section-title">노드</div>

        {/* nodeTypes 배열을 map으로 돌려 노드 아이템들을 동적으로 렌더링합니다. */}
        {nodeTypes.map(node => (
          <div className="node-item" key={node.type}>
            <div className={`node-icon ${node.type}-node`}></div>
            <div className="node-info">
              <div className="node-title">{node.label}</div>
              <div className="node-description">{node.description}</div>
            </div>
            {/* 버튼 클릭 시 App.js의 addNode 함수를 호출합니다. */}
            <button className="add-button" onClick={() => onAddNode(node.type, node.label)}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 5V19M5 12H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
          </div>
        ))}
        
        {/* Version 과 Action Buttons UI는 그대로 유지됩니다. */}
        <div className="section-title">버전</div>
        {/* ... Version Items JSX ... */}

        <div className="action-buttons">
          {/* ... Action Buttons JSX ... */}
        </div>
      </div>
    </div>
  );
}

export default Header;

