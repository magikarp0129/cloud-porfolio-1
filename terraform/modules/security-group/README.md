# Security Group Module

자주 변경되는 security group rule을 inline block이 아닌 독립 resource와 semantic-key map으로 관리합니다.

- `aws_vpc_security_group_ingress_rule` and `aws_vpc_security_group_egress_rule`
- Stable keys such as `alb_https`, `app_to_db`, and `dns_udp`
- Exactly one source or destination per rule
- Create a new security group or attach rules to an existing group
- No implicit allow-all egress rule

한 security group의 rule은 하나의 Terraform state만 소유해야 합니다. Console, 다른 module, 다른 state와 rule ownership을 혼합하지 않습니다.
