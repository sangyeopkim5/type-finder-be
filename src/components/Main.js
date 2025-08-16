import React from 'react';
import './Main.css';

function Main() {
  return (
    <div className="center-canvas" data-node-id="58:456">
      <div className="canvas-grid">
        {/* Problem Analysis Node */}
        <div className="canvas-node problem-node" id="problem-node" data-node-id="59:1282">
          <div className="node-content">
            <svg width="50" height="47" viewBox="0 0 50 47" fill="none" className="magnifying-glass">
              <circle cx="20" cy="20" r="12" stroke="currentColor" strokeWidth="3"/>
              <path d="M28 28L38 38" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
            </svg>
            <div className="node-label">문제 분석 노드</div>
          </div>
          <div className="connection-shapes">
            <svg width="8" height="9" viewBox="0 0 12 14" fill="none" xmlns="http://www.w3.org/2000/svg" className="shape purple-triangle">
              <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#8237D9"/>
            </svg>
            <svg width="8" height="9" viewBox="0 0 12 14" fill="none" xmlns="http://www.w3.org/2000/svg" className="shape green-triangle">
              <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#37D937"/>
            </svg>
            <svg width="8" height="8" viewBox="0 0 13 12" fill="none" xmlns="http://www.w3.org/2000/svg" className="shape purple-circle">
              <circle cx="6.25" cy="6" r="6" fill="#8237D9"/>
            </svg>
            <svg width="8" height="8" viewBox="0 0 16 15" fill="none" xmlns="http://www.w3.org/2000/svg" className="shape blue-square">
              <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
            </svg>
          </div>
        </div>
        <div className="canvas-node concept-canvas-node" id="concept-canvas-node" data-node-id="59:506">
          <div className="node-content">
            <svg width="55" height="54" viewBox="0 0 55 54" fill="none" className="lightbulb">
              <path fillRule="evenodd" clipRule="evenodd" d="M27.25 5.0625C18.0677 5.0625 10.6562 12.4403 10.6562 21.5033C10.6562 26.6175 13.012 31.1895 16.7222 34.2124C17.1238 34.5392 17.4004 34.9946 17.5052 35.5016C17.926 37.5435 18.5178 39.8981 18.9396 41.5159C19.0285 41.8556 19.258 42.0086 19.4762 42.0311C20.9511 42.1774 23.443 42.3416 27.25 42.3416C31.057 42.3416 33.5489 42.1785 35.0238 42.0311C35.242 42.0086 35.4715 41.8556 35.5604 41.5159C35.9822 39.8981 36.5729 37.5435 36.9947 35.5016C37.0994 34.9942 37.376 34.5384 37.7778 34.2113C41.488 31.1906 43.8438 26.6175 43.8438 21.5033C43.8438 12.4403 36.4322 5.0625 27.25 5.0625ZM6.15625 21.5033C6.15625 9.92025 15.6175 0.5625 27.25 0.5625C38.8825 0.5625 48.3438 9.92025 48.3438 21.5033C48.3438 27.7436 45.592 33.345 41.2394 37.1756C40.834 39.0096 40.3926 40.8355 39.9152 42.6521C39.526 44.1427 38.5079 45.4084 37.1073 46.0609L36.9351 47.6471C36.6764 50.0411 34.9574 52.2158 32.326 52.5611C31.0154 52.7332 29.311 52.875 27.25 52.875C25.0821 52.875 23.3991 52.7175 22.1628 52.5319C19.8711 52.1842 18.3647 50.364 17.9823 48.3255C17.863 47.6921 17.7303 46.9564 17.593 46.1497C16.0889 45.5276 14.992 44.2125 14.5847 42.651C14.1074 40.8348 13.666 39.0093 13.2606 37.1756C8.90912 33.345 6.15625 27.7436 6.15625 21.5033ZM37.0938 21.5033C37.0938 18.8925 36.0566 16.3887 34.2106 14.5427C32.3645 12.6966 29.8607 11.6595 27.25 11.6595C26.6533 11.6595 26.081 11.4224 25.659 11.0005C25.2371 10.5785 25 10.0062 25 9.4095C25 8.81276 25.2371 8.24047 25.659 7.81851C26.081 7.39655 26.6533 7.1595 27.25 7.1595C35.1722 7.1595 41.5938 13.581 41.5938 21.5033C41.5938 22.1 41.3567 22.6723 40.9347 23.0942C40.5128 23.5162 39.9405 23.7533 39.3438 23.7533C38.747 23.7533 38.1747 23.5162 37.7528 23.0942C37.3308 22.6723 37.0938 22.1 37.0938 21.5033Z" fill="currentColor"/>
              </svg>
              <div className="node-label">개념 심화 노드</div>
            </div>
            <div className="connection-shapes-left">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape purple-triangle">
                <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#8237D9"/>
              </svg>
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape green-triangle">
                <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#37D937"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape purple-circle">
                <circle cx="6.25" cy="6" r="6" fill="#8237D9"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
            </div>
            <div className="connection-shapes">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape purple-triangle">
                <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#8237D9"/>
              </svg>
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape green-triangle">
                <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#37D937"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape purple-circle">
                <circle cx="6.25" cy="6" r="6" fill="#8237D9"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
            </div>
          </div>
          <div className="canvas-node strategy-node" id="strategy-node" data-node-id="56:328">
            <div className="node-content">
              <svg width="54" height="54" viewBox="0 0 54 54" fill="none" className="compass-icon">
                <mask id="mask0_104_956" style={{maskType:'luminance'}} maskUnits="userSpaceOnUse" x="0" y="0" width="54" height="54">
                  <path d="M27 1.5C41.0817 1.5 52.5 12.9183 52.5 27C52.5 41.0817 41.0817 52.5 27 52.5C12.9183 52.5 1.5 41.0817 1.5 27C1.5 12.9183 12.9183 1.5 27 1.5Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M32.1001 32.1L12.8334 41.1667L21.9001 21.9L41.1667 12.8333L32.1001 32.1Z" fill="white"/>
                  <path d="M27.0001 29.8333C28.5649 29.8333 29.8334 28.5648 29.8334 27C29.8334 25.4352 28.5649 24.1667 27.0001 24.1667C25.4353 24.1667 24.1667 25.4352 24.1667 27C24.1667 28.5648 25.4353 29.8333 27.0001 29.8333Z" fill="black"/>
                </mask>
                <g mask="url(#mask0_104_956)">
                  <path d="M61 -7H-7V61H61V-7Z" fill="currentColor"/>
                </g>
              </svg>
              <div className="node-label">전략 수립 노드</div>
            </div>
            <div className="connection-shapes-left">
               <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape purple-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#8237D9"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                  <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape purple-circle">
                  <circle cx="6.25" cy="6" r="6" fill="#8237D9"/>
              </svg>
            </div>
            <div className="connection-shapes">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape purple-triangle">
                  <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#8237D9"/>
              </svg>
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape green-triangle">
                  <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#37D937"/>
              </svg>
               <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape blue-triangle">
                  <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#009DFF"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                  <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
            </div>
          </div>
          <div className="canvas-node visualization-node" id="visualization-node" data-node-id="56:354">
            <div className="node-content">
              <svg width="55" height="55" viewBox="0 0 55 55" fill="none" className="graph-icon">
                <path d="M36.6666 26.9958L46.3833 10.1979L50.3478 12.4896L38.3624 33.2292L23.4437 24.6354L12.5124 43.5417H50.4166V48.125H4.58325V6.875H9.16659V40.1958L21.7708 18.3333L36.6666 26.9958Z" fill="currentColor"/>
              </svg>
              <div className="node-label">시각화 노드</div>
            </div>
            <div className="connection-shapes-left">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape green-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#37D937"/>
              </svg>
            </div>
            <div className="connection-shapes">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape orange-triangle">
                  <path d="M0.25 7L11.5 0.937822V13.0622L0.25 7Z" fill="#FFA500"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                  <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
            </div>
          </div>
          <div className="canvas-node video-node" id="video-node" data-node-id="56:362">
            <div className="node-content">
              <svg width="77" height="77" viewBox="0 0 77 77" fill="none" className="video-icon">
                <path d="M48.125 25.6667V51.3333H16.0417V25.6667H48.125ZM51.3333 19.25H12.8333C11.9824 19.25 11.1664 19.588 10.5647 20.1897C9.96302 20.7914 9.625 21.6074 9.625 22.4583V54.5417C9.625 55.3926 9.96302 56.2086 10.5647 56.8103C11.1664 57.412 11.9824 57.75 12.8333 57.75H51.3333C52.1842 57.75 53.0003 57.412 53.602 56.8103C54.2036 56.2086 54.5417 55.3926 54.5417 54.5417V43.3125L67.375 56.1458V20.8542L54.5417 33.6875V22.4583C54.5417 21.6074 54.2036 20.7914 53.602 20.1897C53.0003 19.588 52.1842 19.25 51.3333 19.25Z" fill="currentColor"/>
              </svg>
              <div className="node-label">영상화 노드</div>
            </div>
            <div className="connection-shapes-left">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape orange-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#FFA500"/>
              </svg>
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape green-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#37D937"/>
              </svg>
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape blue-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#009DFF"/>
              </svg>
            </div>
            <div className="connection-shapes">
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape orange-circle">
                  <circle cx="6.25" cy="6" r="6" fill="#FFA500"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape blue-square">
                  <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#009DFF"/>
              </svg>
            </div>
          </div>
          <div className="canvas-node summary-node" id="summary-node" data-node-id="56:369">
            <div className="node-content">
              <svg width="71" height="71" viewBox="0 0 71 71" fill="none" className="microphone-icon">
                <path d="M35.4998 41.4167C33.0346 41.4167 30.9391 40.5538 29.2134 38.8281C27.4877 37.1024 26.6248 35.0069 26.6248 32.5417V14.7917C26.6248 12.3264 27.4877 10.2309 29.2134 8.5052C30.9391 6.7795 33.0346 5.91666 35.4998 5.91666C37.9651 5.91666 40.0606 6.7795 41.7863 8.5052C43.512 10.2309 44.3748 12.3264 44.3748 14.7917V32.5417C44.3748 35.0069 43.512 37.1024 41.7863 38.8281C40.0606 40.5538 37.9651 41.4167 35.4998 41.4167ZM32.5415 62.125V53.0281C27.4137 52.3378 23.1734 50.0451 19.8207 46.15C16.4679 42.2549 14.7915 37.7187 14.7915 32.5417H20.7082C20.7082 36.634 22.1509 40.1229 25.0362 43.0082C27.9216 45.8936 31.4094 47.3353 35.4998 47.3333C39.5902 47.3313 43.0791 45.8887 45.9664 43.0053C48.8538 40.1219 50.2955 36.634 50.2915 32.5417H56.2082C56.2082 37.7187 54.5318 42.2549 51.179 46.15C47.8262 50.0451 43.586 52.3378 38.4582 53.0281V62.125H32.5415ZM35.4998 35.5C36.338 35.5 37.0411 35.216 37.6091 34.648C38.1771 34.08 38.4601 33.3779 38.4582 32.5417V14.7917C38.4582 13.9535 38.1742 13.2514 37.6062 12.6853C37.0382 12.1193 36.3361 11.8353 35.4998 11.8333C34.6636 11.8314 33.9615 12.1154 33.3935 12.6853C32.8255 13.2553 32.5415 13.9574 32.5415 14.7917V32.5417C32.5415 33.3799 32.8255 34.0829 33.3935 34.6509C33.9615 35.2189 34.6636 35.502 35.4998 35.5Z" fill="currentColor"/>
              </svg>
              <div className="node-label">요약 노드</div>
            </div>
            <div className="connection-shapes-left">
              <svg width="8" height="9" viewBox="0 0 12 14" fill="none" className="shape orange-triangle">
                  <path d="M11.25 7L0 13.0622V0.937822L11.25 7Z" fill="#FFA500"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape orange-circle">
                  <circle cx="6.25" cy="6" r="6" fill="#FFA500"/>
              </svg>
            </div>
            <div className="connection-shapes">
              <svg width="8" height="8" viewBox="0 0 13 12" fill="none" className="shape blue-circle">
                  <circle cx="6.25" cy="6" r="6" fill="#009DFF"/>
              </svg>
              <svg width="8" height="8" viewBox="0 0 16 15" fill="none" className="shape orange-square">
                  <rect width="10.5015" height="10.5015" transform="matrix(0.711213 -0.702977 0.711213 0.702977 0.3125 7.61768)" fill="#FFA500"/>
              </svg>
            </div>
          </div>
        </div>
        <svg id="connection-layer" width="100%" height="100%" style={{position: 'absolute', top: 0, left: 0, pointerEvents: 'none'}}></svg>
      </div>
    
  );
}

export default Main;