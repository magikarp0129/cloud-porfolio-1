# Route Policy Module

foundation이 생성한 route table에 TGW, VPC peering, inspection, endpoint 같은 추가 경로를 독립 `aws_route` resource로 관리합니다.

- Route table and route ownership are separated by lifecycle.
- Stable map keys prevent list-index churn.
- Exactly one destination and one target are required.
- Default TGW routes remain owned by the foundation network module.

동일 route table의 inline `route` block과 `aws_route` resource를 혼합하지 않습니다. 동일 destination을 여러 state에서 관리하지 않습니다.
