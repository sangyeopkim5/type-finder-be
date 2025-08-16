# M - 콘텐츠 생성 도구 (React 버전)

전통적인 학습 방식을 혁신하는 AI 기반 콘텐츠 생성 플랫폼입니다.

## 🚀 프로젝트 구조

```
src/
├── components/          # React 컴포넌트
│   ├── Header.js       # 왼쪽 사이드바 (노드 목록)
│   ├── Header.css      # Header 컴포넌트 스타일
│   ├── Main.js         # 메인 캔버스 영역
│   ├── Main.css        # Main 컴포넌트 스타일
│   ├── Footer.js       # 하단 푸터
│   └── Footer.css      # Footer 컴포넌트 스타일
├── App.js              # 메인 App 컴포넌트
├── App.css             # App 컴포넌트 스타일
├── index.js            # React 앱 진입점
├── index.css           # 기본 스타일
└── script.js           # 유틸리티 함수들
```

## ✨ 주요 기능

### 🎯 노드 기반 콘텐츠 구성
- **개념 심화 노드**: 개념 심화, 증명, 연관개념
- **전략 수립 노드**: 풀이전략 & 스토리보드
- **시각화 노드**: 그래프, 차트, 다이어그램
- **문제 분석 노드**: 문제 이해 & 분석

### 🔗 연결 시스템
- 다양한 소켓 타입 지원 (보라색 삼각형, 파란색 사각형, 주황색 원, 노란색 다이아몬드)
- 드래그 앤 드롭으로 노드 연결
- 실시간 연결선 렌더링

### 🎨 인터랙티브 UI
- 사이드바 접기/펼치기
- 노드 드래그 앤 드롭
- 실시간 편집
- 반응형 디자인

## 🛠️ 설치 및 실행

### 필수 요구사항
- Node.js 16.0.0 이상
- npm 또는 yarn

### 설치
```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm start

# 프로덕션 빌드
npm run build
```

### 개발 서버
개발 서버는 `http://localhost:3000`에서 실행됩니다.

## 🎮 사용법

### 노드 추가
1. 왼쪽 사이드바에서 원하는 노드 타입의 `+` 버튼 클릭
2. 캔버스에 노드가 생성됩니다

### 노드 연결
1. 노드의 소켓(색깔이 있는 도형)을 클릭
2. 다른 노드의 소켓으로 드래그하여 연결

### 노드 편집
1. 노드를 클릭하여 선택
2. 텍스트 영역에 내용 입력

### 노드 이동
1. 노드를 드래그하여 원하는 위치로 이동

### 사이드바 접기
1. 로고 옆의 접기 버튼 클릭
2. 사이드바가 축소되어 더 넓은 작업 공간 확보

## 🎨 스타일링

프로젝트는 CSS 모듈을 사용하여 컴포넌트별로 스타일을 관리합니다:

- **Header.css**: 사이드바 스타일
- **Main.css**: 캔버스 및 노드 스타일
- **Footer.css**: 푸터 스타일
- **App.css**: 전체 앱 공통 스타일

## 🔧 기술 스택

- **Frontend**: React 18
- **Styling**: CSS3 (CSS Grid, Flexbox)
- **Build Tool**: Create React App
- **Package Manager**: npm

## 📱 반응형 디자인

- 모바일, 태블릿, 데스크톱 지원
- 터치 기반 인터페이스
- 적응형 레이아웃

## 🚀 향후 계획

- [ ] 실시간 협업 기능
- [ ] AI 기반 콘텐츠 생성
- [ ] 노드 템플릿 시스템
- [ ] 데이터 내보내기/가져오기
- [ ] 다크 모드 지원

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

- Email: contact@manion.com
- 전화: 02-1234-5678

---

**M - 콘텐츠 생성 도구**로 더 나은 학습 경험을 만들어보세요! 🎓✨
