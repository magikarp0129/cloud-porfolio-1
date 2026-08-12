# Terraform Module Catalog

현재 17개 module 디렉터리에 Terraform 구현이 있습니다. 환경 이름, account ID, backend와 적용 순서는 root가 결정하며 module은 입력·출력과 resource lifecycle만 소유합니다.

| Module | 소유 범위 | 소유하지 않는 범위 |
| --- | --- | --- |
| [organization](organization/README.md) | AWS Organization과 OU | account vending, Control Tower |
| [scp-policy](scp-policy/README.md) | SCP/Tag Policy와 attachment | 정책 승인과 예외 register |
| [network](network/README.md) | 공통 private VPC, 7개 subnet tier, endpoint와 TGW attachment | 중앙 inspection |
| [service-vpc](service-vpc/README.md) | 서비스 private VPC와 TGW attachment | 중앙 association/route |
| [transit-gateway-hub](transit-gateway-hub/README.md) | TGW, route-table domain과 RAM share | service attachment |
| [transit-gateway-routing](transit-gateway-routing/README.md) | association과 명시적 TGW route | VPC와 attachment 생성 |
| [security-group](security-group/README.md) | 독립 ingress/egress rule | foundation rule 중복 소유 |
| [route-policy](route-policy/README.md) | 기존 route table의 추가 route | 기본 VPC route |
| [workload-environment](workload-environment/README.md) | environment foundation composition | Kubernetes platform state |
| [security](security/README.md) | KMS, EBS/S3 baseline과 detection service | 중앙 audit archive |
| [iam](iam/README.md) | deployment/audit/workload role | 사람 SSO assignment |
| [waf](waf/README.md) | WAF rule, rate limit과 logging | ingress resource 생성 |
| [observability](observability/README.md) | VPC Flow Logs, CloudWatch, SNS와 alarm | EKS log, Prometheus와 중앙 archive |
| [operations](operations/README.md) | Backup, scheduler, patch와 Inspector integration | EKS restore 성공 주장 |
| [cost](cost/README.md) | Budget와 Cost Anomaly Detection | CUR/invoice와 실현 절감 검증 |
| [eks](eks/README.md) | EKS, node/add-on, Pod Identity, KMS와 log | Kubernetes workload와 autoscaler |
| [kubernetes-platform](kubernetes-platform/README.md) | ENIConfig, Istio, Prometheus, quota와 PriorityClass | application release와 실제 PDB instance |

## Composition

```text
organization root
  → organization + scp-policy

environment root
  → workload-environment
       → network + security + iam + observability
       → operations + cost + eks

environment/platform root
  → kubernetes-platform

landing-zone and service roots
  → service-vpc + transit-gateway-hub + transit-gateway-routing
```

각 module README에는 목적, 생성 resource, 중요한 입력·출력, 명시적 제외와 적용 전 조건을 기록합니다. 변수 schema는 `variables.tf`, output은 `outputs.tf`가 source of truth입니다.

검증은 실제 작업할 root에서 표준 Terraform 명령으로 수행합니다.

```bash
terraform fmt -check
terraform init -backend=false
terraform validate
```
