import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.js';
import './index.css'; // 전역 스타일 또는 App.css를 불러옵니다.

// 1. public/index.html 파일에서 id가 'root'인 요소를 찾습니다.
const rootElement = document.getElementById('root');

// 2. React가 제어할 수 있는 'root'를 생성합니다.
const root = ReactDOM.createRoot(rootElement);


// 3. 생성된 root에 App 컴포넌트를 렌더링(그려넣기)합니다.
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);