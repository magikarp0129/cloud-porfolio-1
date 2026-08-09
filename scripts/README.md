# 실행 스크립트 안내

이 디렉터리는 사람이 직접 실행하거나 CI가 호출하는 진입점만 둡니다. 실제 AWS·Kubernetes 자원 정의는 `terraform/`, 에이전트 실행 로직은 `agent-runtime/`가 소유하며, `scripts/`는 이를 검증하거나 읽기 전용 운영 증적을 수집하고 문서를 빌드합니다.

## 책임별 구조

```text
scripts/
|-- README.md
|-- agent/
|   `-- agentctl.py                     # 읽기 전용 장애 분석 CLI
|-- validation/
|   |-- validate-terraform.sh           # Terraform 전체 정적 검증 진입점
|   |-- validate-monitoring-alert-policy.py
|   |-- verify-report-library.py       # report template/example과 Schema 경계 검증
|   |-- verify-architecture-diagram.py
|   `-- verify-service-network-plan.py
|-- operations/
|   |-- linux/
|   |   |-- README.md                   # 증상별 명령·queue·자원 압박 판단 가이드
|   |   |-- system-health-report.sh
|   |   |-- network-pressure-report.sh # socket queue·drop·retransmit·conntrack
|   |   |-- resource-pressure-report.sh # CPU·memory·FD·disk·I/O pressure
|   |   |-- service-triage.sh
|   |   `-- patch-readiness.sh
|   |-- kubernetes/
|   |   `-- eks-cluster-health.sh
|   `-- aws/
|       `-- audit-cloudwatch-log-retention.sh
|-- pdf/
|   |-- build/                          # 포트폴리오·구성도 PDF 생성기
|   `-- verify/                         # PDF 텍스트·페이지·렌더링 검수
|-- lib/
|   `-- common.sh                       # Bash 공통 입력·출력 안전 검사
`-- tests/
    |-- validate-operations-scripts.sh
    `-- fakes/                          # AWS·kubectl 모의 응답
```

| 영역 | 사용 주체 | 생성하거나 확인하는 것 | 인프라 변경 |
| --- | --- | --- | --- |
| `agent/` | 운영자, 에이전트 CI | 요청 계약 검증과 장애 분석 보고서 | 없음 |
| `validation/` | 개발자, pull request CI | Terraform·구성도·CIDR·알람 정책 일관성 | 없음 |
| `operations/` | 인프라 운영자 | Linux, EKS, CloudWatch Logs의 현재 상태 증적 | 없음 |
| `pdf/build/` | 문서 담당자 | 최상위 포트폴리오 PDF와 선택적 비교 산출물 | 없음 |
| `pdf/verify/` | 문서 담당자, CI | PDF 텍스트, 페이지, 렌더링 품질 | 없음 |
| `lib/`, `tests/` | 스크립트 개발자 | 공통 안전 검사와 모의 회귀 시험 | 없음 |

`scripts/` 안에 Python 파일이 많은 이유는 에이전트 요청 계약, Markdown-to-PDF 빌드, PDF 텍스트 검증처럼 구조화된 데이터 처리가 필요하기 때문입니다. Linux와 인프라 운영 명령은 `operations/` 아래 Bash로 분리해 목적을 바로 식별할 수 있게 했습니다.

## 주요 실행 명령

에이전트 요청과 모의 장애 증적을 검증합니다.

```bash
python3 scripts/agent/agentctl.py validate \
  --request examples/incidents/prod-api-5xx-request.json \
  --config config/monitoring/runtime.example.json
```

Terraform 형식, 배포 root, 구성도와 서비스 CIDR을 검증합니다.

```bash
./scripts/validation/validate-terraform.sh
```

모니터링 query와 Warning/Critical 임계값 계약을 검증합니다.

```bash
python3 scripts/validation/validate-monitoring-alert-policy.py
```

월간·장애 보고서 양식, sanitized example과 incident Schema 핵심 경계를 검증합니다.

```bash
python3 scripts/validation/verify-report-library.py
```

현재 포트폴리오를 만들고 검수합니다.

```bash
python3 scripts/pdf/build/build_portfolio_presentation_pdf.py
python3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf
```

## 읽기 전용 운영 점검

Linux 장애 상황에서 어떤 스크립트를 먼저 실행하고 `ss`, `netstat`, `top`, `vmstat`, `file-nr`, `iostat` 결과를 어떻게 해석할지는 [Linux 장애 분석 스크립트와 판단 가이드](operations/linux/README.md)를 기준으로 합니다.

### Linux 호스트 상태

```bash
sudo ./scripts/operations/linux/system-health-report.sh \
  --since "2 hours ago" \
  --output /var/tmp/system-health.txt
```

`sudo`는 systemd journal이나 프로세스 소켓까지 확인해야 할 때만 사용합니다. journal에 애플리케이션이 잘못 기록한 민감정보가 있을 수 있으므로 공유 전 검토가 필요합니다.

### 트래픽·socket queue 압박

```bash
sudo ./scripts/operations/linux/network-pressure-report.sh \
  --sample-seconds 5 \
  --listen-queue-warning 80 \
  --output /var/tmp/network-pressure.txt
```

`ss`를 우선 사용해 listen/established queue, TCP state, retransmit, interface drop, softnet backlog와 conntrack 사용량을 수집하며 `ss`가 없으면 `netstat`으로 제한적으로 대체합니다.

### CPU·메모리·파일 디스크립터·I/O 압박

```bash
sudo ./scripts/operations/linux/resource-pressure-report.sh \
  --sample-seconds 5 \
  --top 20 \
  --output /var/tmp/resource-pressure.txt
```

`top`, `vmstat`, PSI, `MemAvailable`, swap·OOM, 시스템과 프로세스별 file descriptor, block·inode 사용량, `iostat`, 삭제 후 열린 파일을 한 보고서에 모읍니다. 단일 시점 결과는 원인 확정이 아니므로 모니터링 추세와 함께 판단합니다.

### systemd 서비스 장애 분석

```bash
sudo ./scripts/operations/linux/service-triage.sh \
  --service nginx.service \
  --since "30 minutes ago" \
  --output /var/tmp/nginx-triage.txt
```

### 패치 사전 점검

```bash
sudo ./scripts/operations/linux/patch-readiness.sh \
  --output /var/tmp/patch-readiness.txt
```

로컬 패키지 메타데이터만 읽습니다. 실제 설치 전에는 승인된 저장소 갱신, 백업, 이중화, 유지보수 창과 원복 계획을 별도로 확인합니다.

### EKS 상태 점검

```bash
./scripts/operations/kubernetes/eks-cluster-health.sh \
  --context arn:aws:eks:ap-northeast-2:123456789012:cluster/prod-platform \
  --namespace payments \
  --output /var/tmp/eks-health.txt
```

현재 context를 암묵적으로 사용하지 않고 `--context`를 필수로 받으며 Secret과 ConfigMap 내용은 조회하지 않습니다.

### CloudWatch Logs 보존 감사

```bash
./scripts/operations/aws/audit-cloudwatch-log-retention.sh \
  --region ap-northeast-2 \
  --profile audit-readonly \
  --prefix /aws/eks/ \
  --minimum-days 90 \
  --require-kms \
  --fail-on-findings
```

정책 위반 시 종료 코드 `2`를 반환합니다. 이 도구는 설정을 고치지 않으며 수정은 검토된 Terraform 변경으로 수행합니다.

## 안전 원칙과 시험

- 서버, kubeconfig context, AWS region과 profile을 명시합니다.
- Secret, ConfigMap 내용, 전체 환경 변수와 프로세스 환경은 수집하지 않습니다.
- 보고서 파일은 `umask 077`로 만들고 심볼릭 링크 출력은 거부합니다.
- 패키지 설치, `kubectl apply/delete/patch/scale/cordon/drain`, AWS create/update/put/delete API를 실행하지 않습니다.
- 조회 결과는 `internal` 또는 `confidential`로 분류해 승인된 티켓 저장소에 보관합니다.
- 발견된 문제는 Terraform pull request와 사람 승인 절차로 전달합니다.

운영 스크립트 회귀 시험은 다음 명령으로 실행합니다.

```bash
bash scripts/tests/validate-operations-scripts.sh
```

이 시험은 Bash 구문, 도움말, `eval` 금지, CloudWatch 보존 위반 종료 코드, 명시적 EKS context를 모의 응답으로 확인합니다. 네트워크·자원 압박 스크립트는 Linux `/proc`, `ss`, `vmstat` 등에 의존하므로 syntax와 help를 CI에서 확인하고 실제 수집은 승인된 비운영 Linux에서 별도 통합 시험합니다.

## 생성 파일 경계

`__pycache__/`, `.pdf-tools/`, Terraform provider cache와 장애 보고서 출력은 소스가 아닙니다. Git에 포함하지 않고 재생성 가능하게 유지합니다. 최종 제출용 PDF만 저장소 최상위 `enterprise-cloud-portfolio.pdf`로 생성합니다.
