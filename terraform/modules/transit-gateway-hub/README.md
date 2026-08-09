# Transit Gateway Hub Module

Network account에서 엔터프라이즈 Transit Gateway와 `nonprod`, `prod`, `shared`, `inspection` route table을 생성합니다.

- 기본 association/propagation을 끕니다.
- RAM으로 Organization, OU 또는 account에 TGW를 공유합니다.
- 실제 service attachment의 association과 route는 `transit-gateway-routing` module이 중앙에서 관리합니다.
- Organization 전체 공유를 사용할 경우 management account에서 AWS RAM organization sharing을 먼저 활성화해야 합니다.
