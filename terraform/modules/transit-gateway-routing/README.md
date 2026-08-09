# Transit Gateway Routing Module

서비스 계정과 공통 EKS 환경 root가 만든 TGW attachment ID를 Network account의 별도 state로 전달받아 중앙에서 association과 route를 관리합니다.

- `dev`와 `stg`는 `nonprod`, `prod`는 `prod` route table에 연결합니다.
- 기본 full-mesh propagation은 사용하지 않습니다.
- 서비스 간 경로는 `allowed_routes`에 명시한 CIDR만 생성합니다.
- Inspection/Shared Services attachment가 있으면 return route를 중앙 route table에 생성합니다.
