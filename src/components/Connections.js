import React, { useState, useEffect } from 'react';

function Connections({ nodes, connections, canvasRef }) {
  const [paths, setPaths] = useState([]);

  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0 || connections.length === 0) {
      setPaths([]);
      return;
    };

    const canvasRect = canvasRef.current.getBoundingClientRect();
    
    const newPaths = connections.map(conn => {
      const fromNodeEl = document.getElementById(conn.from.nodeId);
      const toNodeEl = document.getElementById(conn.to.nodeId);

      if (!fromNodeEl || !toNodeEl) return null;
      
      const fromRect = fromNodeEl.getBoundingClientRect();
      const toRect = toNodeEl.getBoundingClientRect();

      const startX = fromRect.left + fromRect.width - canvasRect.left;
      const startY = fromRect.top + fromRect.height / 2 - canvasRect.top;
      const endX = toRect.left - canvasRect.left;
      const endY = toRect.top + toRect.height / 2 - canvasRect.top;

      const d = `M ${startX} ${startY} C ${startX + 50} ${startY}, ${endX - 50} ${endY}, ${endX} ${endY}`;
      
      return {
        key: `path-${conn.from.nodeId}-${conn.to.nodeId}`,
        d: d,
        stroke: conn.color,
      };
    }).filter(p => p !== null);

    setPaths(newPaths);

  }, [nodes, connections, canvasRef]);

  return (
    <svg 
      id="connection-layer" 
      width="100%" 
      height="100%" 
      style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
    >
      {paths.map(path => (
        <path
          key={path.key}
          d={path.d}
          stroke={path.stroke}
          strokeWidth="2.5"
          fill="none"
          style={{ filter: `drop-shadow(0 1px 2px ${path.stroke}60)` }}
        />
      ))}
    </svg>
  );
}

export default Connections;