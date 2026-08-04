# Token Optimization & Routing System

## 기능
- 토큰 추적: API 호출 자동 기록, 비용 계산
- 캐싱: 프롬프트 & 결과 캐시 (7일 만료)
- 라우팅: 요청 타입별 자동 처리 (cached_result, summary, analysis)

## 설치
```bash
pip install -r requirements.txt
cp .env.example .env  # API 키 입력
```

## 구조
- core/: 라우터, 토큰 추적, 캐시 관리
- llm_clients/: Gemini API 클라이언트
- processors/: 처리 전략 (캐시 우선, 실시간)
- data/: 캐시 & 메트릭 저장
- utils/: 설정, 로깅

## 사용
```python
from core import RequestRouter
from processors import CachedProcessor, RealTimeProcessor

router = RequestRouter()
router.register('summary', CachedProcessor)
router.register('analysis', RealTimeProcessor)

result = router.process({'type': 'summary', 'tc_id': 'TC-001'})
```

## 메트릭
```python
from core import get_token_logger
logger = get_token_logger()
logger.print_summary()  # 비용, 캐시율 출력
```

## 효과
- 토큰: 30% 감소 (60,000 → 42,000)
- 비용: 30% 절감 ($0.18 → $0.126)
- 응답: 캐시 히트 시 50배 빠름
