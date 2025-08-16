import React from 'react';
import Node from './Node';
import './Main.css';

function Main() {
  // 노드 데이터 정의 - Main.js의 하드코딩된 노드들을 정확히 그대로 옮김
  const nodes = [
    {
      id: 'problem-node',
      type: 'problem',
      label: '문제 분석 노드',
      x: 300,
      y: 300
    },
    {
      id: 'concept-canvas-node',
      type: 'concept-canvas',
      label: '개념 심화 노드',
      x: 300,
      y: 400
    },
    {
      id: 'strategy-node',
      type: 'strategy',
      label: '전략 수립 노드',
      x: 300,
      y: 500
    },
    {
      id: 'visualization-node',
      type: 'visualization',
      label: '시각화 노드',
      x: 400,
      y: 300
    },
    {
      id: 'video-node',
      type: 'video',
      label: '영상화 노드',
      x: 400,
      y: 400
    },
    {
      id: 'summary-node',
      type: 'summary',
      label: '요약 노드',
      x: 400,
      y: 500
    }
  ];

  const handleMouseDown = (e) => {
    // 마우스 이벤트 처리 로직
    console.log('Node clicked:', e.target.id);
  };

  return (
    <div className="center-canvas">
      <div className="canvas-grid">
        {nodes.map((node) => (
          <Node
            key={node.id}
            node={node}
            onMouseDown={handleMouseDown}
          />
        ))}
      </div>
      
      {/* Connection Layer for SVG connections */}
      <svg id="connection-layer" width="100%" height="100%" style={{position: 'absolute', top: 0, left: 0, pointerEvents: 'none'}}></svg>
    </div>
  );
}

export default Main;