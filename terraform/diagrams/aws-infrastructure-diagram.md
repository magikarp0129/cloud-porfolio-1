# Terraform 코드 기준 AWS 인프라 구성도

현재 `terraform/` 구현을 Mermaid로 표현합니다. 초록은 코드 구현, 노랑은 외부 입력·검증 필요, 회색 점선은 미구현 목표입니다.

## 1. AWS Organizations와 환경 경계

```mermaid
flowchart TB
    ORG["AWS Organizations"]:::ok --> SEC["Security OU"]:::ok
    ORG --> INFRA["Infrastructure OU"]:::ok
    ORG --> WORK["Workloads OU"]:::ok
    WORK --> DEV["Dev 환경 root<br/>VPC 10.10.0.0/16 · 2 AZ<br/>Landing Zone TGW<br/>EKS 1.35<br/>Control/Container 로그 90/30일<br/>Prometheus 7일 · Backup 14일<br/>업무시간 Scheduler 사용"]:::ok
    WORK --> STG["Stg 환경 root<br/>VPC 10.15.0.0/16 · 2 AZ<br/>Landing Zone TGW<br/>EKS 1.35<br/>Control/Container 로그 90/90일<br/>Prometheus 15일 · Backup 35일<br/>업무시간 Scheduler 사용"]:::ok
    WORK --> PROD["Prod 환경 root<br/>VPC 10.20.0.0/16 · 3 AZ<br/>Landing Zone TGW<br/>EKS 1.35<br/>Control/Container 로그 365/365일<br/>Prometheus 30일 · Backup 35일<br/>Vault Lock · Scheduler 미사용"]:::ok
    NOTE["aws_organizations_account<br/>현재 환경 root에 없음"]:::target -.-> WORK
    classDef ok fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:2px;
    classDef target fill:#F4F5F7,stroke:#8993A4,color:#5E6C84,stroke-dasharray:5 5;
```

## 2. 환경별 VPC와 통신 흐름

```mermaid
flowchart LR
    USER["사내·외부 사용자"]:::ext --> EDGE["Landing Zone 중앙 ingress<br/>검사·egress attachment는 입력 필요"]:::partial
    EDGE --> TGW["Enterprise TGW"]:::ok
    subgraph VPC["Workload Private VPC · Public/IGW/NAT 없음"]
      TGWS["TGW Subnet<br/>attachment"]:::ok
      LB["LB Subnet<br/>내부 ALB/NLB"]:::ok
      AP["AP Subnet<br/>application ENI"]:::ok
      NODE["Node Subnet<br/>EKS managed node"]:::ok
      POD["Pod Subnet<br/>VPC CNI secondary ENI"]:::ok
      DB["DB Subnet<br/>기업 CIDR만 TGW"]:::ok
      CLUSTER["EKS Cluster Subnet<br/>control-plane x-ENI"]:::ok
      VPCE["S3·Interface Endpoint"]:::ok
      TGWS --> LB --> AP
      AP --> DB
      NODE --> POD
      CLUSTER --> NODE
      NODE --> VPCE
    end
    TGW --> TGWS
    classDef ok fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:2px;
    classDef partial fill:#FFF7D6,stroke:#FFAB00,color:#172B4D,stroke-width:2px;
    classDef ext fill:#DEEBFF,stroke:#0052CC,color:#172B4D,stroke-width:2px;
```

LB/AP/Node/Pod/EKS Cluster subnet의 기본 경로는 TGW를 향합니다. DB subnet에는 인터넷 기본 경로가 없습니다.

## 3. EKS 상태와 플랫폼 소유권

```mermaid
flowchart LR
    subgraph F["Foundation State"]
      CL["Private EKS 1.35<br/>EKS Cluster Subnet"]:::ok
      NG["Managed Node Group<br/>Node Subnet · AL2023"]:::ok
      CNI["VPC CNI<br/>custom networking<br/>prefix delegation"]:::ok
      ADD["EKS Managed Add-on 6종"]:::ok
      LOG["Control 5종 · Container 4종<br/>CloudWatch Logs"]:::ok
      CL --> NG --> CNI
      CL --> ADD
      CL --> LOG
    end
    subgraph P["Kubernetes Platform State"]
      ENI["AZ별 ENIConfig<br/>Pod Subnet + Cluster SG"]:::ok
      ISTIO["Istio · 내부 LoadBalancer<br/>strict mTLS"]:::ok
      POLICY["ResourceQuota · LimitRange<br/>PriorityClass"]:::ok
      MON["Prometheus · Grafana<br/>Alertmanager"]:::ok
      ENI --> ISTIO --> POLICY
    end
    subgraph A["Application Release State"]
      APP["Deployment · Service<br/>requests/limits · probe"]:::target
      SCALE["HPA/KEDA · PDB · topology"]:::target
    end
    CNI --> ENI
    POLICY -.-> APP --> SCALE
    CA["Cluster Autoscaler/Karpenter<br/>현재 controller 미구현"]:::target -.-> NG
    ALBC["AWS Load Balancer Controller<br/>미설치"]:::target -.-> ISTIO
    classDef ok fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:2px;
    classDef target fill:#F4F5F7,stroke:#8993A4,color:#5E6C84,stroke-dasharray:5 5;
```

Terraform이 `desired_size` drift를 무시하는 것은 autoscaler 설치를 뜻하지 않습니다.

## 4. 관측·운영·변경 통제 흐름

```mermaid
flowchart TB
    SIG["EKS Logs · Container Insights<br/>VPC Flow Logs · Prometheus"]:::ok --> OBS["CloudWatch · Grafana"]:::ok
    OBS --> HUMAN["Platform Operations 검토<br/>ticket · 영향 · 원복"]:::human
    HUMAN --> CICD["PR → Plan → 승인 → CI/CD<br/>작업 도구의 prod 직접 apply 금지"]:::human
    CICD --> VERIFY["사후 검증과 보고서"]:::human
    BACKUP["AWS Backup · Vault Lock"]:::ok --> HUMAN
    ALERT["Alertmanager receiver/route 미구성"]:::partial -.-> OBS
    ARCH["중앙 불변 Log Archive 미구현"]:::target -.-> OBS
    classDef ok fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:2px;
    classDef partial fill:#FFF7D6,stroke:#FFAB00,color:#172B4D,stroke-width:2px;
    classDef target fill:#F4F5F7,stroke:#8993A4,color:#5E6C84,stroke-dasharray:5 5;
    classDef human fill:#EAE6FF,stroke:#6554C0,color:#172B4D,stroke-width:2px;
```

## 5. 서비스 Landing Zone과 Transit Gateway

```mermaid
flowchart TB
    IPAM["IPAM 10.64.0.0/10"]:::ok --> SVC["5 services × dev/stg/prod<br/>15 private VPC"]:::ok
    TGW["Enterprise TGW · ASN 64520<br/>nonprod · prod · shared · inspection RT"]:::ok --> SVC
    SVC --> C["commerce"]:::ok
    SVC --> P["payments"]:::ok
    SVC --> A["analytics"]:::ok
    SVC --> CP["customer-profile"]:::ok
    SVC --> IA["internal-admin"]:::ok
    INSP["중앙 ingress/egress·inspection attachment<br/>배포 입력 필요"]:::target -.-> TGW
    classDef ok fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:2px;
    classDef target fill:#F4F5F7,stroke:#8993A4,color:#5E6C84,stroke-dasharray:5 5;
```

## 6. IPAM과 서비스별 VPC 크기

```mermaid
flowchart TB
    E["10.64.0.0/10"]:::root
    E --> C["commerce<br/>prod 10.65.0.0/16"]:::pool
    E --> P["payments<br/>prod 10.73.0.0/18"]:::pool
    E --> A["analytics<br/>prod 10.77.0.0/16"]:::pool
    E --> CP["customer-profile<br/>prod 10.81.0.0/19"]:::pool
    E --> IA["internal-admin<br/>prod 10.84.16.0/20"]:::pool
    classDef root fill:#EAE6FF,stroke:#6554C0,color:#172B4D,stroke-width:2px;
    classDef pool fill:#DEEBFF,stroke:#0052CC,color:#172B4D,stroke-width:2px;
```

## 7. 서비스 VPC의 AZ별 Subnet 예시

`commerce-prod 10.65.0.0/16`의 Terraform 계산 결과입니다.

```mermaid
flowchart TB
    VPC["commerce-prod · 3 AZ"]:::vpc
    VPC --> AZ1["apne2-az1<br/>Pod 10.65.0.0/19<br/>Node 10.65.128.0/20<br/>AP 10.65.176.0/21<br/>DB 10.65.200.0/22<br/>LB 10.65.212.0/22<br/>TGW 10.65.255.160/28<br/>EKS x-ENI 10.65.255.208/28"]:::az
    VPC --> AZ2["apne2-az2<br/>Pod 10.65.32.0/19<br/>Node 10.65.144.0/20<br/>AP 10.65.184.0/21<br/>DB 10.65.204.0/22<br/>LB 10.65.216.0/22<br/>TGW 10.65.255.176/28<br/>EKS x-ENI 10.65.255.224/28"]:::az
    VPC --> AZ3["apne2-az3<br/>Pod 10.65.64.0/19<br/>Node 10.65.160.0/20<br/>AP 10.65.192.0/21<br/>DB 10.65.208.0/22<br/>LB 10.65.220.0/22<br/>TGW 10.65.255.192/28<br/>EKS x-ENI 10.65.255.240/28"]:::az
    AZ1 --> TGW["Landing Zone TGW<br/>중앙 ingress·egress"]:::tgw
    AZ2 --> TGW
    AZ3 --> TGW
    classDef vpc fill:#EAE6FF,stroke:#6554C0,color:#172B4D,stroke-width:2px;
    classDef az fill:#E3FCEF,stroke:#00875A,color:#172B4D,stroke-width:1.5px;
    classDef tgw fill:#FFF7D6,stroke:#FFAB00,color:#172B4D,stroke-width:2px;
```

환경 입력이나 subnet 계산을 변경하면 Terraform 코드, Mermaid, 검색용 tree와 draw.io 원본을 함께 검토합니다.
