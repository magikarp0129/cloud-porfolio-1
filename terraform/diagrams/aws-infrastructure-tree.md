# Terraform 코드 기준 AWS 인프라 구성 트리

Mermaid 구성도의 검색·검토용 텍스트 표현입니다.

## 1. 전체 구성

```text
AWS Organizations
├── Security OU
├── Infrastructure OU
└── Workloads OU
    ├── dev  · VPC 10.10.0.0/16 · 2 AZ · Landing Zone TGW
    ├── stg  · VPC 10.15.0.0/16 · 2 AZ · Landing Zone TGW
    └── prod · VPC 10.20.0.0/16 · 3 AZ · Landing Zone TGW
```

`aws_organizations_account`는 현재 환경 root에 없습니다.

## 2. 환경 root의 공통 조립 구조

```text
workload-environment
├── network
│   ├── private VPC
│   ├── LB subnet            · 내부 ALB/NLB
│   ├── AP subnet            · application ENI
│   ├── DB subnet            · 기업 CIDR만 TGW
│   ├── Node subnet          · EKS managed node
│   ├── Pod subnet           · VPC CNI secondary ENI
│   ├── TGW subnet           · VPC attachment
│   ├── EKS Cluster subnet   · control-plane x-ENI
│   ├── S3 / Interface Endpoint
│   └── Public subnet · Internet Gateway · NAT Gateway 없음
├── security / IAM
├── observability / operations / cost
├── EKS foundation
└── monitoring-agent-access
```

## 3. 환경별 차이

```text
Dev
├── VPC 10.10.0.0/16 · 2 AZ · Landing Zone TGW
├── EKS 1.35 · Spot 1/1/3
├── Control/Container 로그 90/30일
└── Prometheus 7일 · Backup 14일 · 업무시간 Scheduler 사용

Stg
├── VPC 10.15.0.0/16 · 2 AZ · Landing Zone TGW
├── EKS 1.35 · On-Demand 2/2/5
├── Control/Container 로그 90/90일
└── Prometheus 15일 · Backup 35일 · 업무시간 Scheduler 사용

Prod
├── VPC 10.20.0.0/16 · 3 AZ · Landing Zone TGW
├── EKS 1.35 · system 3/3/6 + application 3/3/12
├── Control/Container 로그 365/365일
└── Prometheus 30일 · Backup 35일 · Vault Lock · Scheduler 미사용
```

## 4. 네트워크 통신 트리

```text
사내·외부 사용자
└── Landing Zone 중앙 ingress / inspection
    └── Enterprise TGW
        └── TGW subnet
            ├── LB subnet → 내부 ALB/NLB
            │   └── AP subnet → application
            ├── EKS Cluster subnet → control-plane x-ENI
            ├── Node subnet → managed node primary ENI
            │   └── Pod subnet → VPC CNI secondary ENI
            └── DB subnet → 기업 CIDR만 TGW
```

## 5. EKS 구성과 상태 소유권

```text
Foundation state
├── Private EKS 1.35 · EKS Cluster subnet
├── Managed Node Group · Node subnet
├── VPC CNI custom networking · prefix delegation
├── Managed Add-on 6종
└── CloudWatch Logs

Platform state
├── AZ별 ENIConfig · Pod subnet + EKS cluster security group
├── Istio · 내부 LoadBalancer · strict mTLS
├── ResourceQuota · LimitRange · PriorityClass
└── Prometheus · Grafana · Alertmanager

Application state
├── Deployment / StatefulSet / Service
├── requests/limits / probes / PDB / topology
└── HPA/KEDA
```

AWS Load Balancer Controller와 Cluster Autoscaler/Karpenter는 현재 controller 미구현입니다. `desired_size` drift ignore는 autoscaler 설치를 뜻하지 않습니다.

## 6. 관측·운영 흐름

```text
EKS/Container/VPC Flow Logs → CloudWatch → Monitoring Agent 읽기 전용 query
Prometheus → Grafana → Alertmanager(receiver/route 미구성)
운영자 검토 → PR → Plan → 승인 → 보호된 CI/CD
Agent의 prod 직접 apply 금지
```

## 7. 서비스 Landing Zone

```text
IPAM 10.64.0.0/10
└── 5 services × dev/stg/prod = 15 private VPC
    ├── commerce          · prod 10.65.0.0/16
    ├── payments          · prod 10.73.0.0/18
    ├── analytics         · prod 10.77.0.0/16
    ├── customer-profile  · prod 10.81.0.0/19
    └── internal-admin    · prod 10.84.16.0/20

Enterprise TGW
├── nonprod / prod / shared / inspection route table
└── 중앙 ingress/egress·inspection attachment는 배포 입력 필요
```

## 8. 현재 구현이 아닌 항목

```text
AWS 계정 생성 · 중앙 inspection attachment · 중앙 불변 로그 아카이브
서비스 application/RDS · HPA/KEDA · node autoscaler · 실제 PDB instance
```
