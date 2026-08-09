#!/usr/bin/env python3

"""Build ten portfolio samples with genuinely different narrative structures."""

from pathlib import Path
import sys
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_DIR = REPO_ROOT / ".pdf-tools" / "samples" / "content-strategy"
FONT_SANS = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")
FONT_SERIF = Path("/System/Library/Fonts/Supplemental/AppleMyungjo.ttf")
FONT_UNICODE = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")

INK = colors.HexColor("#18232D")
MUTED = colors.HexColor("#5C6975")
LINE = colors.HexColor("#D7DEE4")
PAPER = colors.HexColor("#FFFFFF")
SOFT = colors.HexColor("#F3F6F8")
AMBER = colors.HexColor("#B87916")
RED = colors.HexColor("#A84444")
GREEN = colors.HexColor("#2E7654")


COMMON_FACTS = [
    (
        "환경 3",
        "dev·stg·prod라는 논리 workload 환경을 뜻한다. 각 환경에 AWS 기반 root와 Kubernetes platform root가 분리되어 있다.",
        "실제 AWS 계정 3개에 배포 완료됐다는 뜻은 아니다.",
    ),
    (
        "Terraform 모듈 15",
        "terraform/modules의 16개 디렉터리 중 .tf 구현이 있는 15개를 센다. compute는 향후 EC2/ECS 확장용 예약 디렉터리라 제외한다.",
        "15개 모듈 모두의 실계정 적용과 운영 준비를 증명하지 않는다.",
    ),
    (
        "Terraform 검증 10/10",
        "organization, dev/stg/prod 기반, dev/stg/prod platform 등 7개 root와 security-group·route-policy·waf 3개 모듈이 init -backend=false 및 validate를 통과했다.",
        "실계정 plan/apply, 권한, 용량, 비용 검증은 별도다.",
    ),
    (
        "에이전트 시험 24/24",
        "요청 계약 9건, 보안 경계 8건, 장애 분석 5건, Terraform 권한 경계 2건의 로컬 자동 시험이 통과했다.",
        "live AWS/EKS 연결, MTTR 개선, 운영 정확도를 증명하지 않는다.",
    ),
]


STRATEGIES = [
    {
        "slug": "01-engineering-report",
        "name": "01 표준 엔지니어링 보고서형",
        "english": "ENGINEERING REPORT",
        "accent": "#087E8B",
        "font": "sans",
        "ideal": "채용 제출, 기술 검토, 범용 포트폴리오",
        "purpose": "문제에서 시작해 설계·구현·검증·한계로 수렴하는 가장 정석적인 기술 보고서",
        "voice": "객관적이고 순차적인 설명",
        "toc": [
            ("1. 문제와 범위", ["1.1 운영 복잡성", "1.2 설계 범위", "1.3 숫자 산정 기준"]),
            ("2. 설계 원칙", ["2.1 상태 분리", "2.2 권한 경계", "2.3 실패 범위 축소"]),
            ("3. 구현", ["3.1 Organizations", "3.2 Terraform", "3.3 EKS 운영"]),
            ("4. 검증", ["4.1 10/10 검증", "4.2 24/24 시험", "4.3 증적 해석"]),
            ("5. 한계와 다음 단계", ["5.1 미검증 항목", "5.2 운영 전환 조건"]),
        ],
        "pages": [
            {
                "kicker": "1 · PROBLEM AND SCOPE",
                "title": "먼저 무엇을 해결하려는지 설명한다",
                "question": "계정·네트워크·Kubernetes·운영 정책의 생명주기가 다른데, 왜 하나의 상태와 배포 흐름으로 관리하면 위험한가?",
                "lead": "이 포트폴리오는 엔터프라이즈 클라우드 구축을 단순 리소스 생성이 아니라 변경 실패의 범위를 줄이는 플랫폼 설계 문제로 다룬다.",
                "sections": [
                    ("문제 정의", "조직 정책, 공통 네트워크, EKS 플랫폼, 워크로드 운영은 변경 주체와 승인자가 다르다. 모든 구성을 한 root에 묶으면 작은 수정도 넓은 plan과 권한을 요구한다."),
                    ("해결 방향", "organization root, 환경별 AWS 기반 root, 환경별 platform root를 분리하고 reusable module을 연결한다. prod 직접 apply 대신 protected CI/CD가 plan artifact와 승인을 확인한다."),
                    ("범위 읽기", "환경 3과 모듈 15는 코드의 구조적 범위다. 10/10과 24/24는 현재 등록된 자동 검증 집합의 통과 상태다."),
                ],
            },
            {
                "kicker": "4 · VALIDATION",
                "title": "구현 뒤에 검증과 해석 제한을 둔다",
                "question": "현재 저장소가 실제로 입증하는 것과 아직 입증하지 못한 것은 무엇인가?",
                "lead": "검증 결과를 구현 성과와 분리해 제시하면 자동 시험 통과를 운영 완료로 오해하는 일을 줄일 수 있다.",
                "sections": [
                    ("확인된 것", "Terraform 대상 10/10과 에이전트 로컬 시험 24/24가 통과했다. 환경 분리, 모듈 입력·출력, 요청 계약과 보안 경계가 코드와 시험으로 확인된다."),
                    ("남은 것", "실제 AWS 계정의 plan/apply, EKS restore drill, 장애 대응 리허설, 실측 비용과 KPI는 별도 운영 증적이 필요하다."),
                    ("결론 방식", "보고서는 ‘설계됨’, ‘로컬 검증됨’, ‘실환경 검증 필요’를 구분해 다음 단계의 승인 조건으로 연결한다."),
                ],
            },
        ],
        "closing_title": "보고서의 결론: 구현 범위와 운영 증적을 분리한다",
        "closing_note": "가장 익숙하고 균형 잡힌 형식이다. 다만 의사결정의 갈등이나 개인의 문제 해결 과정은 다른 형식보다 덜 선명할 수 있다.",
    },
    {
        "slug": "02-problem-solving-case-study",
        "name": "02 문제 해결 사례연구형",
        "english": "PROBLEM-SOLVING CASE STUDY",
        "accent": "#B24C3D",
        "font": "serif",
        "ideal": "면접관에게 사고 과정과 선택 이유를 보여줄 때",
        "purpose": "상황·제약·대안·선택·결과·교훈 순으로 엔지니어의 문제 해결 과정을 드러내는 사례연구",
        "voice": "맥락과 판단을 강조하는 서술",
        "toc": [
            ("1. 상황", ["1.1 조직과 플랫폼", "1.2 운영 복잡성", "1.3 성공 조건"]),
            ("2. 제약", ["2.1 권한", "2.2 상태", "2.3 prod 승인"]),
            ("3. 검토한 선택지", ["3.1 단일 root", "3.2 환경만 분리", "3.3 계층 분리"]),
            ("4. 선택과 실행", ["4.1 선택 이유", "4.2 구현 흐름", "4.3 검증 결과"]),
            ("5. 회고", ["5.1 잘된 점", "5.2 남은 위험", "5.3 다시 한다면"]),
        ],
        "pages": [
            {
                "kicker": "SITUATION → CONSTRAINT",
                "title": "문제의 긴장을 먼저 보여준다",
                "question": "빠르게 구축하면서도 prod의 변경 권한과 장애 범위를 어떻게 좁힐 것인가?",
                "lead": "상황은 멀티환경 플랫폼의 일관성이 필요하다는 것이고, 제약은 모든 변경을 한 번에 수행할 수 없다는 것이다.",
                "sections": [
                    ("상황", "dev·stg·prod에서 네트워크, EKS, 관측성, 운영 정책을 반복 가능하게 제공해야 했다. 동시에 조직 정책과 workload 플랫폼의 책임자는 서로 다르다."),
                    ("핵심 제약", "prod 직접 apply를 허용하지 않고, short-lived credential과 지정 승인자를 거치는 흐름이 필요했다. 실제 계정 없이도 구조와 경계를 검토 가능해야 했다."),
                    ("성공 기준", "작은 변경이 불필요한 상태까지 흔들지 않고, 자동 검증의 분모와 한계를 읽는 사람이 바로 이해할 수 있어야 했다."),
                ],
            },
            {
                "kicker": "OPTIONS → CHOICE → RESULT",
                "title": "버린 대안까지 써야 선택이 설득력을 얻는다",
                "question": "왜 단일 Terraform root나 환경만 나눈 구조를 선택하지 않았는가?",
                "lead": "사례연구형은 정답만 제시하지 않고 대안의 장단점을 비교한 뒤 현재 구조가 어떤 제약에 가장 잘 맞았는지 설명한다.",
                "sections": [
                    ("대안 A · 단일 root", "초기 진입은 쉽지만 조직 정책과 EKS 변경이 같은 상태와 권한을 공유한다. blast radius와 plan 가독성이 커져 제외했다."),
                    ("대안 B · 환경만 분리", "dev·stg·prod 격리는 되지만 환경 안에서 AWS 기반과 Kubernetes 오브젝트의 변경 주기를 여전히 묶는다."),
                    ("선택 · 계층 분리", "organization, environment AWS, platform root를 분리하고 15개 구현 모듈을 조합했다. 결과는 10/10 Terraform 검증과 24/24 에이전트 시험으로 확인했다."),
                ],
            },
        ],
        "closing_title": "사례연구의 결론: 무엇을 만들었는지보다 왜 그렇게 만들었는지",
        "closing_note": "개인의 판단과 학습을 잘 보여준다. 반면 전체 기술 항목을 사전처럼 빠르게 찾는 용도에는 표준 보고서보다 불리하다.",
    },
    {
        "slug": "03-architecture-decision-pack",
        "name": "03 아키텍처 의사결정 기록형",
        "english": "ARCHITECTURE DECISION PACK",
        "accent": "#2B67A0",
        "font": "sans",
        "ideal": "시니어 엔지니어·아키텍트 리뷰, 설계 인터뷰",
        "purpose": "하나의 긴 설명 대신 핵심 선택을 ADR 단위로 쪼개 결정·대안·결과를 추적하는 문서",
        "voice": "결정 중심의 간결한 기록",
        "toc": [
            ("ADR-001 상태 경계", ["상태", "결정", "결과"]),
            ("ADR-002 Private EKS", ["접근 경계", "운영 경로", "trade-off"]),
            ("ADR-003 배포 승인", ["prod 금지", "protected CI/CD", "감사 연결"]),
            ("ADR-004 에이전트 도입", ["read-first", "bounded delegation", "승격 조건"]),
            ("결정 증적", ["검증 수치", "미검증 위험", "재검토 trigger"]),
        ],
        "pages": [
            {
                "kicker": "ADR-001 · ACCEPTED",
                "title": "Terraform 상태를 책임과 생명주기로 분리한다",
                "question": "어떤 경계를 기준으로 state와 권한을 나눌 것인가?",
                "lead": "결정: organization, environment AWS, Kubernetes platform을 서로 다른 root와 state로 관리한다.",
                "sections": [
                    ("맥락", "조직 정책은 전사 guardrail이고, VPC·EKS는 환경 기반이며, Kubernetes 정책과 관측성은 플랫폼 운영 주기가 더 빠르다."),
                    ("검토한 대안", "단일 state는 단순하지만 권한과 blast radius가 크다. 환경별 state만으로는 Kubernetes와 AWS 기반의 변경 속도 차이를 흡수하기 어렵다."),
                    ("결과", "구조는 복잡해지지만 plan 범위, 승인자, 장애 격리와 소유권이 명확해진다. root 간 output 계약 관리가 새 운영 과제가 된다."),
                ],
            },
            {
                "kicker": "ADR-004 · STAGED ADOPTION",
                "title": "AI 에이전트는 read에서 시작해 증거로 승격한다",
                "question": "에이전트가 prod를 직접 변경하지 않으면서 실무 가치를 만들려면 어떤 단계가 필요한가?",
                "lead": "결정: Human-led, Agent-assisted를 시작점으로 하고 use case×environment별 증적에 따라 draft, review, bounded delegation으로 승격한다.",
                "sections": [
                    ("통제", "AI Gateway가 identity, model allowlist, tool boundary, token quota를 확인한다. 모든 변경은 branch·patch·PR 또는 protected pipeline으로 전달한다."),
                    ("근거", "요청 계약 9건, 보안 경계 8건, 장애 분석 5건, Terraform 경계 2건으로 구성된 24/24 로컬 시험이 현재의 최소 증적이다."),
                    ("재검토 조건", "live 연결, 오탐·누락, 비용, MTTR, 승인 지연 데이터가 쌓이면 권한과 자동화 단계를 다시 결정한다."),
                ],
            },
        ],
        "closing_title": "ADR의 결론: 결정은 고정된 정답이 아니라 재검토 가능한 약속",
        "closing_note": "설계 근거와 trade-off가 가장 선명하다. 구현 세부를 연속적으로 학습하려는 독자에게는 ADR 사이의 연결 설명이 추가로 필요하다.",
    },
    {
        "slug": "04-interview-portfolio",
        "name": "04 기술면접 대화형",
        "english": "INTERVIEW PORTFOLIO",
        "accent": "#6A4FA3",
        "font": "sans",
        "ideal": "기술면접, 포트폴리오 발표, 15분 설명",
        "purpose": "90초 요약과 예상 질문·답변을 중심으로 면접 대화 흐름에 맞춘 문서",
        "voice": "짧고 직접적인 1인칭 설명",
        "toc": [
            ("0. 90초 요약", ["문제", "내 선택", "검증"]),
            ("1. 가장 중요한 결정", ["state 분리", "private EKS", "prod 승인"]),
            ("2. 왜 이렇게 했나요?", ["대안", "trade-off", "실패 범위"]),
            ("3. 직접 확인한 것은?", ["10/10", "24/24", "코드 위치"]),
            ("4. 다음 질문", ["운영 전환", "개선안", "실환경 증적"]),
        ],
        "pages": [
            {
                "kicker": "90-SECOND OPENING",
                "title": "첫 페이지에서 프로젝트 전체를 말할 수 있게 한다",
                "question": "이 프로젝트를 90초 안에 설명해 보세요.",
                "lead": "저는 멀티환경 AWS·EKS 플랫폼을 Terraform으로 재현하면서, 변경 권한과 상태의 경계를 운영 책임에 맞춰 분리했습니다.",
                "sections": [
                    ("제가 해결한 문제", "조직 정책부터 Kubernetes 운영까지 한 흐름에 묶일 때 생기는 넓은 권한과 blast radius를 줄이는 문제였습니다."),
                    ("제가 한 핵심 선택", "organization, dev/stg/prod AWS 기반, 각 platform root를 나누고 15개 구현 모듈로 공통 기준을 재사용했습니다."),
                    ("제가 확인한 범위", "Terraform 등록 대상 10/10과 에이전트 시험 24/24를 통과시켰습니다. 다만 live plan/apply와 restore drill은 다음 검증 단계로 명시했습니다."),
                ],
            },
            {
                "kicker": "EXPECTED QUESTIONS",
                "title": "본문은 예상 질문과 답으로 전개한다",
                "question": "왜 environment root와 platform root를 또 나눴나요?",
                "lead": "AWS 기반과 Kubernetes 오브젝트는 변경 속도, 도구 권한, 승인자, 장애 영향이 다르기 때문입니다.",
                "sections": [
                    ("Q · 단일 root가 더 단순하지 않나요?", "A · 초기에는 단순하지만 작은 Kubernetes 정책 변경이 VPC·EKS state와 권한까지 건드릴 수 있습니다. 저는 운영 단순성보다 변경 격리의 이점을 선택했습니다."),
                    ("Q · 숫자 15와 10/10은 어떤 관계인가요?", "A · 15는 구현된 reusable module 수이고, 10은 검증 스크립트가 직접 실행하는 root·독립 모듈 대상 수입니다. 같은 분모가 아닙니다."),
                    ("Q · 가장 먼저 보완할 것은요?", "A · 실계정 plan, EKS 복구 훈련, 장애 리허설을 실행해 설계 증적을 운영 증적으로 전환하겠습니다."),
                ],
            },
        ],
        "closing_title": "면접형의 결론: 독자가 다음 질문을 쉽게 고르게 한다",
        "closing_note": "발표와 대화에는 가장 강하다. 감사 문서나 공식 설계 기준으로 재사용하려면 표와 정책 원문을 부록으로 보강해야 한다.",
    },
    {
        "slug": "05-production-readiness-review",
        "name": "05 프로덕션 준비도 검토형",
        "english": "PRODUCTION READINESS REVIEW",
        "accent": "#277454",
        "font": "unicode",
        "ideal": "Go/No-Go 리뷰, 운영 인수, 출시 전 점검",
        "purpose": "구현 설명보다 운영 gate·현재 상태·차단 항목을 먼저 보여주는 준비도 검토 문서",
        "voice": "판정과 조치 중심",
        "toc": [
            ("1. 판정 요약", ["현재 판정", "근거", "조건부 항목"]),
            ("2. 필수 gate", ["보안", "복구", "관측성", "변경 관리"]),
            ("3. 준비도 매트릭스", ["Ready", "Conditional", "Not evidenced"]),
            ("4. 운영 리허설", ["restore drill", "incident drill", "rollback"]),
            ("5. Go/No-Go 조건", ["차단 항목", "승인자", "증적 위치"]),
        ],
        "pages": [
            {
                "kicker": "READINESS VERDICT · CONDITIONAL",
                "title": "설계 완료가 아니라 운영 가능 여부부터 판정한다",
                "question": "이 저장소를 근거로 지금 prod 배포를 승인할 수 있는가?",
                "lead": "판정: 조건부. 구조와 로컬 자동 검증은 검토 가능하지만 실계정과 복구 증적이 없어 prod Go 판정에는 부족하다.",
                "sections": [
                    ("READY · 코드 구조", "dev·stg·prod 분리, 15개 구현 모듈, protected CI/CD 경계와 운영 책임이 문서화되어 있다."),
                    ("CONDITIONAL · 자동 검증", "Terraform 10/10과 에이전트 24/24는 통과했다. 검증 분모가 제한되어 있으므로 staging plan과 실제 권한 검사가 필요하다."),
                    ("NOT EVIDENCED · 운영 훈련", "EKS backup/restore, incident escalation, rollback, 비용 budget 동작과 KPI 실측 결과는 아직 운영 증적이 없다."),
                ],
            },
            {
                "kicker": "GATES AND OWNERS",
                "title": "차단 항목에는 완료 조건과 책임자를 붙인다",
                "question": "무엇이 완료되어야 Conditional이 Go로 바뀌는가?",
                "lead": "각 gate는 문서 존재가 아니라 실행 결과, 승인자, artifact 위치까지 확인해야 닫힌다.",
                "sections": [
                    ("Gate 1 · Staging plan", "CI/CD Agent가 immutable plan artifact를 만들고 Architecture·Security reviewer가 네트워크, IAM, KMS 변경을 승인한다."),
                    ("Gate 2 · Restore drill", "Operations Agent가 백업 복구 시간을 측정하고 RPO/RTO 충족 여부와 실패 로그를 runbook에 남긴다."),
                    ("Gate 3 · Incident rehearsal", "Monitoring·Operations Agent가 경보→triage→escalation→복구 흐름을 리허설하고 trace_id로 증적을 연결한다."),
                ],
            },
        ],
        "closing_title": "준비도형의 결론: 배포 가능 여부와 차단 사유를 한눈에",
        "closing_note": "운영 인수와 출시 판단에 적합하다. 프로젝트의 배경과 창작 과정을 보여주는 포트폴리오 서사로는 다소 건조하다.",
    },
    {
        "slug": "06-evidence-led-audit",
        "name": "06 증적 중심 감사형",
        "english": "EVIDENCE-LED AUDIT PACK",
        "accent": "#4D5966",
        "font": "sans",
        "ideal": "보안·거버넌스 리뷰, 통제 검증, 외부 감사 대응",
        "purpose": "주장을 먼저 쓰고 근거·소유자·한계·잔여 위험을 대응시키는 감사 친화적 문서",
        "voice": "검증 가능하고 보수적인 표현",
        "toc": [
            ("1. 주장 등록부", ["claim ID", "통제 목적", "상태"]),
            ("2. 증적 매핑", ["코드", "시험", "문서", "artifact"]),
            ("3. 책임 매핑", ["owner", "reviewer", "approver"]),
            ("4. 예외와 한계", ["미검증", "보상 통제", "만료일"]),
            ("5. 잔여 위험", ["위험 등급", "조치", "재검토일"]),
        ],
        "pages": [
            {
                "kicker": "CLAIM REGISTER",
                "title": "‘안전하다’ 대신 검증 가능한 주장을 쓴다",
                "question": "각 설계 주장은 어떤 코드·시험·승인 기록으로 확인할 수 있는가?",
                "lead": "감사형은 서술보다 claim ID를 중심으로 통제 목적과 증적의 연결을 우선한다.",
                "sections": [
                    ("CLM-001 · 상태 격리", "주장: 조직, 환경 AWS, platform 변경은 독립 root로 분리된다. 증적: terraform/organization 및 terraform/environments/*/platform 구조."),
                    ("CLM-002 · prod 직접 변경 금지", "주장: 에이전트는 prod에 직접 apply하지 않는다. 증적: 역할 정의, protected CI/CD 승인 경계, Terraform 권한 경계 시험 2건."),
                    ("CLM-003 · 요청 추적", "주장: 요청·tool call·승인·artifact는 request_id와 trace_id로 연결하도록 설계되었다. 한계: live telemetry 보존 결과는 미검증."),
                ],
            },
            {
                "kicker": "EVIDENCE AND EXCEPTIONS",
                "title": "통과 수치 옆에 예외와 잔여 위험을 둔다",
                "question": "10/10과 24/24가 통과했어도 어떤 위험은 남는가?",
                "lead": "감사에서는 PASS가 통제의 전체 유효성을 의미하지 않는다. 시험 범위와 실환경 차이를 예외로 등록한다.",
                "sections": [
                    ("EVD-010 · Terraform", "등록된 10개 대상은 init -backend=false 및 validate를 통과했다. 실제 provider 권한, remote state lock, 조직 SCP 충돌은 실계정 시험이 필요하다."),
                    ("EVD-024 · Agent runtime", "24개 로컬 시험은 계약·보안·triage·권한 경계를 확인한다. live tool 호출과 오탐·누락률은 측정되지 않았다."),
                    ("RSK-007 · 운영 복구", "backup, patch, CVE/EOS 기준은 문서화되어 있으나 복구 리허설 artifact가 없다. prod 승인 전 차단 위험으로 유지한다."),
                ],
            },
        ],
        "closing_title": "감사형의 결론: 주장·증적·한계가 한 행에서 만난다",
        "closing_note": "통제 검증에는 강하지만 읽는 재미와 프로젝트의 전체 맥락은 약하다. 채용 포트폴리오에서는 요약 서사를 앞에 붙이는 편이 좋다.",
    },
    {
        "slug": "07-business-outcome-narrative",
        "name": "07 비즈니스 성과 연결형",
        "english": "BUSINESS OUTCOME NARRATIVE",
        "accent": "#9B6A16",
        "font": "serif",
        "ideal": "리더십 리뷰, 투자 우선순위, 기술-사업 연결 설명",
        "purpose": "기술 기능을 운영 성과 가설·KPI·검증 책임으로 연결하는 결과 중심 문서",
        "voice": "성과 가설과 책임을 명시하는 설명",
        "toc": [
            ("1. 사업 문제", ["변경 리드타임", "감사 부담", "장애 비용"]),
            ("2. 플랫폼 능력", ["표준화", "격리", "자동 검증"]),
            ("3. 성과 가설", ["리드타임", "change failure", "MTTR", "비용"]),
            ("4. 측정 설계", ["baseline", "owner", "evidence"]),
            ("5. 투자 로드맵", ["증적 확보", "운영 자동화", "확장 조건"]),
        ],
        "pages": [
            {
                "kicker": "BUSINESS PROBLEM → CAPABILITY",
                "title": "리소스 목록이 아니라 운영 결과에서 시작한다",
                "question": "이 플랫폼이 조직의 변경 속도·안전성·감사 비용에 어떤 영향을 줄 수 있는가?",
                "lead": "기술 구현은 그 자체가 성과가 아니다. 상태 격리와 표준 모듈은 더 작은 변경, 더 명확한 승인, 반복 가능한 검증을 가능하게 하는 능력이다.",
                "sections": [
                    ("문제 · 넓은 변경 범위", "서로 다른 생명주기의 리소스를 한 흐름으로 관리하면 리뷰 시간이 늘고 실패 시 영향 범위가 커질 수 있다."),
                    ("능력 · 경계가 있는 플랫폼", "환경 3, 구현 모듈 15, root 계층 분리는 표준을 재사용하면서 plan과 권한 범위를 좁히는 기반을 제공한다."),
                    ("기대 결과 · 가설", "변경 리드타임 감소, change failure rate 개선, 감사 추적 시간 단축을 기대할 수 있다. 현재는 설계 가설이며 실측값이 아니다."),
                ],
            },
            {
                "kicker": "KPI → EVIDENCE → OWNER",
                "title": "좋아질 것이라는 주장에 측정 책임을 붙인다",
                "question": "어떤 데이터가 쌓여야 플랫폼의 사업 가치를 주장할 수 있는가?",
                "lead": "성과형 문서는 수치를 과장하지 않고 baseline, 측정식, accountable validator와 증적 위치를 함께 정의한다.",
                "sections": [
                    ("변경 성과", "배포 요청부터 승인까지의 lead time, rollback 비율, 실패 변경 건수를 CI/CD artifact로 측정한다. Owner: CI/CD Agent와 Operations."),
                    ("운영 성과", "alert acknowledgement, triage 시간, restore time, SLO 위반을 telemetry와 incident record로 측정한다. Owner: Monitoring과 Operations."),
                    ("현재 선행 지표", "Terraform 10/10과 에이전트 24/24는 자동화 가능한 품질 경계의 선행 지표다. 사업 KPI의 실제 개선을 대신하지 않는다."),
                ],
            },
        ],
        "closing_title": "성과형의 결론: 기술 자산을 측정 가능한 운영 가설로 번역한다",
        "closing_note": "비기술 리더와의 대화에 강하다. 모듈 입력값이나 세부 운영 절차를 확인하려는 엔지니어에게는 기술 부록이 필요하다.",
    },
    {
        "slug": "08-platform-product-document",
        "name": "08 플랫폼 제품 설명서형",
        "english": "PLATFORM AS A PRODUCT",
        "accent": "#19716F",
        "font": "sans",
        "ideal": "내부 개발자 플랫폼 소개, 사용자 온보딩, 서비스 카탈로그",
        "purpose": "인프라 구성보다 사용자·서비스·golden path·지원 모델을 중심으로 플랫폼을 하나의 제품처럼 설명",
        "voice": "사용자 과업 중심",
        "toc": [
            ("1. 사용자와 요구", ["애플리케이션 팀", "플랫폼 운영자", "보안 reviewer"]),
            ("2. 서비스 카탈로그", ["Landing zone", "EKS", "관측성", "운영"]),
            ("3. Golden path", ["요청", "plan", "승인", "배포"]),
            ("4. 서비스 수준", ["SLO", "지원 경계", "비상 절차"]),
            ("5. 제품 로드맵", ["현재", "다음", "졸업 조건"]),
        ],
        "pages": [
            {
                "kicker": "USERS AND JOBS TO BE DONE",
                "title": "플랫폼을 누가 어떤 일을 위해 쓰는지부터 설명한다",
                "question": "애플리케이션 팀이 안전한 EKS 환경을 얻기 위해 거쳐야 할 최소 경로는 무엇인가?",
                "lead": "플랫폼은 Terraform 저장소가 아니라 표준 환경, 승인 흐름, 관측성과 운영 지원을 묶어 제공하는 내부 서비스다.",
                "sections": [
                    ("애플리케이션 팀", "환경과 용량 요구를 제출하고 승인된 module input을 사용한다. 조직 SCP나 공통 네트워크를 직접 변경하지 않는다."),
                    ("플랫폼 운영자", "dev·stg·prod 기반과 platform root를 운영하고 EKS, 로그, 메트릭, autoscaling, backup 정책의 golden path를 유지한다."),
                    ("보안·거버넌스 reviewer", "identity, data classification, encryption, prod approval과 정책 예외를 검토하고 evidence를 request_id에 연결한다."),
                ],
            },
            {
                "kicker": "SERVICE CATALOG AND GOLDEN PATH",
                "title": "기술 장 대신 제공 서비스와 사용자 여정을 보여준다",
                "question": "플랫폼이 현재 제공하는 서비스와 아직 제공을 약속하지 않는 것은 무엇인가?",
                "lead": "카탈로그는 제공 범위와 지원 경계를 명확하게 해 사용자 기대를 관리한다.",
                "sections": [
                    ("서비스 · Landing zone", "Organizations, OU, SCP, tag policy의 구조와 environment 기반을 제공한다. 실제 조직 반영은 승인된 CI/CD 실행이 필요하다."),
                    ("서비스 · Managed EKS baseline", "private endpoint, KMS, control plane log, AL2023 node, namespace 운영 기준을 코드와 문서로 제공한다."),
                    ("현재 제품 상태", "15개 구현 모듈과 10/10 검증이 서비스 구성의 선행 증적이다. live SLO와 지원 처리 시간은 아직 제품 지표로 축적되지 않았다."),
                ],
            },
        ],
        "closing_title": "제품형의 결론: 무엇이 있는가보다 사용자가 어떻게 안전하게 소비하는가",
        "closing_note": "내부 사용자 관점과 채택 전략에 강하다. 저수준 설계 판단을 평가하려면 ADR 또는 기술 부록을 함께 제공하는 편이 좋다.",
    },
    {
        "slug": "09-incident-scenario-runbook",
        "name": "09 장애 시나리오 런북형",
        "english": "INCIDENT SCENARIO RUNBOOK",
        "accent": "#B05B2B",
        "font": "unicode",
        "ideal": "운영 역량 시연, 장애 대응 리뷰, runbook 교육",
        "purpose": "정상 아키텍처 설명 대신 실제 장애 시나리오를 따라 관측·판단·복구·예방 통제를 보여주는 문서",
        "voice": "시간 순서와 실행 중심",
        "toc": [
            ("1. 사건", ["증상", "영향", "초기 가설"]),
            ("2. 탐지", ["로그", "메트릭", "trace", "경보"]),
            ("3. 진단", ["T+5", "T+15", "에스컬레이션"]),
            ("4. 복구", ["완화", "rollback", "restore"]),
            ("5. 예방", ["guardrail", "시험", "backlog"]),
        ],
        "pages": [
            {
                "kicker": "SCENARIO · EKS WORKLOAD DEGRADATION",
                "title": "정상 구조 대신 장애가 발생한 순간에서 시작한다",
                "question": "배포 직후 pod pending과 지연 증가가 동시에 발생하면 누가 무엇을 먼저 확인하는가?",
                "lead": "T+0 경보 발생. 영향 범위를 namespace·node·cluster·AWS 기반 순으로 좁히고 변경 artifact와 telemetry를 연결한다.",
                "sections": [
                    ("T+0 · 탐지", "Prometheus local 수집과 장기 저장, EKS control plane·node/runtime·workload log에서 증상을 확인한다. PII와 cardinality 경계를 유지한다."),
                    ("T+5 · 첫 분기", "최근 배포, resource quota, PriorityClass, PDB/topology, autoscaling ownership을 확인한다. 에이전트는 read-only triage 초안을 만들고 사람이 판단한다."),
                    ("T+15 · 에스컬레이션", "플랫폼 문제면 Monitoring→Operations→Architecture 경로로, workload 문제면 애플리케이션 owner로 넘긴다. request_id와 trace_id를 유지한다."),
                ],
            },
            {
                "kicker": "RECOVERY → LEARNING",
                "title": "복구 절차 뒤에 설계 통제의 의미를 연결한다",
                "question": "어떤 기존 설계가 장애를 줄이고, 어떤 부분은 아직 시험되지 않았는가?",
                "lead": "런북형은 각 아키텍처 요소를 장애 대응 행동과 연결해 운영 가능성을 설명한다.",
                "sections": [
                    ("격리와 rollback", "environment AWS와 platform root 분리는 변경 범위를 좁힌다. protected CI/CD의 plan artifact로 직전 변경과 승인자를 추적한다."),
                    ("자동화 경계", "에이전트 triage 시험 5건을 포함한 24/24 로컬 시험은 기본 분기를 확인한다. 실제 사고 정확도와 MTTR 개선은 아직 미측정이다."),
                    ("예방 조치", "restore drill, upgrade gate, capacity rehearsal, alert tuning을 실행하고 결과를 운영 증적으로 남겨야 문서화된 기준이 production readiness로 전환된다."),
                ],
            },
        ],
        "closing_title": "런북형의 결론: 아키텍처를 장애 순간의 행동으로 번역한다",
        "closing_note": "운영 역량과 책임 경계를 생생하게 보여준다. 전체 플랫폼의 정상 구조와 모든 구현 항목을 빠짐없이 설명하는 데에는 별도 참조 장이 필요하다.",
    },
    {
        "slug": "10-maturity-roadmap",
        "name": "10 성숙도 로드맵형",
        "english": "MATURITY ROADMAP",
        "accent": "#315A8B",
        "font": "sans",
        "ideal": "현재 상태와 향후 계획, 단계적 자동화 전략 설명",
        "purpose": "완성품처럼 포장하지 않고 현재 baseline에서 운영 증적과 제한된 위임으로 발전하는 단계를 보여주는 문서",
        "voice": "현재·다음·졸업 조건 중심",
        "toc": [
            ("Stage 0 · Baseline", ["문제", "현재 위험", "최소 기준"]),
            ("Stage 1 · Foundation", ["환경", "모듈", "정책 경계"]),
            ("Stage 2 · Verified", ["10/10", "24/24", "검증 한계"]),
            ("Stage 3 · Operational", ["plan", "restore", "incident evidence"]),
            ("Stage 4 · Bounded delegation", ["승격 조건", "rollback", "성과 검증"]),
        ],
        "pages": [
            {
                "kicker": "STAGE 0 → 2 · CURRENT",
                "title": "현재 성숙도를 과장 없이 위치시킨다",
                "question": "이 프로젝트는 설계, 검증, 운영, 자율화 가운데 지금 어느 단계에 있는가?",
                "lead": "현재 위치: Foundation을 구축하고 로컬 Verified 단계까지 도달했다. Operational과 bounded delegation은 아직 증적을 쌓아야 한다.",
                "sections": [
                    ("Stage 1 · Foundation", "dev·stg·prod 환경, 15개 구현 Terraform 모듈, 조직·보안·모니터링·운영 책임과 protected deployment 경계를 정의했다."),
                    ("Stage 2 · Verified", "Terraform 대상 10/10, 에이전트 시험 24/24를 통과했다. 이는 정적·로컬 경계의 검증이지 production 운영 완료가 아니다."),
                    ("현재의 의미", "재현 가능한 구조와 검토 가능한 통제는 갖췄다. 다음 단계는 live system에서 동일한 가정이 유지되는지 확인하는 것이다."),
                ],
            },
            {
                "kicker": "STAGE 3 → 4 · NEXT",
                "title": "다음 단계에는 활동이 아니라 졸업 조건을 쓴다",
                "question": "무엇을 실행하고 어떤 증적이 있어야 더 높은 자동화 단계로 승격할 수 있는가?",
                "lead": "성숙도는 Agent 전체가 아니라 use case×environment 조합별로 관리하며, 실패 시 이전 단계로 돌아갈 수 있어야 한다.",
                "sections": [
                    ("Stage 3 · Operational", "staging plan/apply, EKS restore drill, incident rehearsal, 비용·latency·error telemetry를 실행한다. 지정 approver가 artifact를 검증하면 졸업한다."),
                    ("Stage 4 · Bounded delegation", "반복적이고 저위험인 변경만 제한된 권한·예산·rollback 조건 아래 위임한다. prod 직접 apply 금지는 유지한다."),
                    ("성과 검증", "lead time, change failure rate, MTTR, 비용, 오탐·누락을 baseline과 비교한다. 성과가 없거나 위험이 커지면 권한을 축소한다."),
                ],
            },
        ],
        "closing_title": "로드맵형의 결론: 완료 선언 대신 다음 승격의 증거를 제시한다",
        "closing_note": "정직한 현재 상태와 발전 경로를 보여준다. 이미 완성된 결과물의 강한 인상을 원하는 독자에게는 결론이 다소 보수적으로 느껴질 수 있다.",
    },
]


def register_fonts():
    for path in (FONT_SANS, FONT_SERIF, FONT_UNICODE):
        if not path.exists():
            raise FileNotFoundError(f"Required font not found: {path}")
    pdfmetrics.registerFont(TTFont("StrategySans", str(FONT_SANS)))
    pdfmetrics.registerFont(TTFont("StrategySerif", str(FONT_SERIF)))
    pdfmetrics.registerFont(TTFont("StrategyUnicode", str(FONT_UNICODE)))


def title_font(strategy):
    if strategy["font"] == "serif":
        return "StrategySerif"
    if strategy["font"] == "unicode":
        return "StrategyUnicode"
    return "StrategySans"


def styles_for(strategy):
    accent = colors.HexColor(strategy["accent"])
    heading_font = title_font(strategy)
    return {
        "cover_kicker": ParagraphStyle(
            "cover-kicker", fontName="StrategySans", fontSize=8.5, leading=12,
            textColor=accent, tracking=1.1, spaceAfter=13,
        ),
        "cover_title": ParagraphStyle(
            "cover-title", fontName=heading_font, fontSize=29, leading=38,
            textColor=INK, spaceAfter=16, wordWrap="CJK",
        ),
        "cover_body": ParagraphStyle(
            "cover-body", fontName="StrategySans", fontSize=10.5, leading=18,
            textColor=MUTED, spaceAfter=9, wordWrap="CJK",
        ),
        "kicker": ParagraphStyle(
            "page-kicker", fontName="StrategySans", fontSize=7.8, leading=11,
            textColor=accent, tracking=0.8, spaceAfter=7,
        ),
        "h1": ParagraphStyle(
            "page-h1", fontName=heading_font, fontSize=22, leading=30,
            textColor=INK, spaceAfter=11, wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "page-h2", fontName="StrategySans", fontSize=11.5, leading=17,
            textColor=accent, spaceAfter=5, wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "page-body", fontName="StrategySans", fontSize=9.3, leading=15.5,
            textColor=INK, spaceAfter=7, wordWrap="CJK",
        ),
        "question": ParagraphStyle(
            "page-question", fontName=heading_font, fontSize=11.2, leading=18,
            textColor=INK, backColor=colors.HexColor("#F2F5F7"), borderPadding=11,
            spaceAfter=12, wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "page-small", fontName="StrategySans", fontSize=7.6, leading=12,
            textColor=MUTED, wordWrap="CJK",
        ),
        "toc": ParagraphStyle(
            "toc", fontName="StrategySans", fontSize=9.5, leading=14,
            textColor=INK, wordWrap="CJK",
        ),
        "toc_sub": ParagraphStyle(
            "toc-sub", fontName="StrategySans", fontSize=8.2, leading=13,
            textColor=MUTED, wordWrap="CJK",
        ),
        "metric": ParagraphStyle(
            "metric", fontName="StrategySans", fontSize=7.6, leading=12,
            textColor=INK, wordWrap="CJK",
        ),
        "center": ParagraphStyle(
            "center", fontName="StrategySans", fontSize=8, leading=12,
            textColor=MUTED, alignment=TA_CENTER, wordWrap="CJK",
        ),
    }


class StrategyDocTemplate(BaseDocTemplate):
    def __init__(self, filename, strategy):
        self.strategy = strategy
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title=f"포트폴리오 문서 구성 시안 - {strategy['name']}",
            author="클라우드 플랫폼 엔지니어링 포트폴리오",
            subject=strategy["purpose"],
        )
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="strategy", frames=[frame], onPage=self.draw_page))

    def draw_page(self, canvas, doc):
        width, height = A4
        accent = colors.HexColor(self.strategy["accent"])
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        if doc.page == 1:
            canvas.setFillColor(accent)
            canvas.rect(0, 0, 7 * mm, height, stroke=0, fill=1)
            canvas.setFillColor(colors.HexColor("#EDF2F5"))
            canvas.rect(width - 55 * mm, 0, 55 * mm, 32 * mm, stroke=0, fill=1)
            canvas.setFillColor(accent)
            canvas.rect(width - 35 * mm, height - 24 * mm, 15 * mm, 2 * mm, stroke=0, fill=1)
            canvas.restoreState()
            return

        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.55)
        canvas.line(22 * mm, height - 12 * mm, width - 22 * mm, height - 12 * mm)
        canvas.setFont("StrategySans", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(22 * mm, height - 9 * mm, self.strategy["name"])
        canvas.drawRightString(width - 22 * mm, 9 * mm, f"{doc.page:02d} / 05")
        canvas.setFillColor(accent)
        canvas.rect(22 * mm, 8.2 * mm, 13 * mm, 1.3 * mm, stroke=0, fill=1)
        bookmarks = {
            2: ("상세목차", "contents"),
            3: (self.strategy["pages"][0]["title"], "body-1"),
            4: (self.strategy["pages"][1]["title"], "body-2"),
            5: (self.strategy["closing_title"], "closing"),
        }
        if doc.page in bookmarks:
            label, suffix = bookmarks[doc.page]
            key = f"{self.strategy['slug']}-{suffix}"
            canvas.bookmarkPage(key)
            canvas.addOutlineEntry(label, key, level=0, closed=False)
        canvas.restoreState()


def cover_story(strategy, styles):
    return [
        Spacer(1, 43 * mm),
        Paragraph(f"CONTENT STRATEGY SAMPLE · {escape(strategy['english'])}", styles["cover_kicker"]),
        Paragraph(escape(strategy["name"]), styles["cover_title"]),
        Paragraph(escape(strategy["purpose"]), styles["cover_body"]),
        Spacer(1, 12 * mm),
        info_table(strategy, styles),
        Spacer(1, 34 * mm),
        Paragraph(
            "이 시안은 색과 표지만 바꾼 레이아웃 비교가 아닙니다. 동일한 저장소 사실을 서로 다른 질문, 목차, 근거 배치와 결론 방식으로 다시 작성한 문서 구성 비교본입니다.",
            styles["small"],
        ),
        PageBreak(),
    ]


def info_table(strategy, styles):
    rows = [
        [Paragraph("권장 용도", styles["small"]), Paragraph(escape(strategy["ideal"]), styles["body"])],
        [Paragraph("서술 목소리", styles["small"]), Paragraph(escape(strategy["voice"]), styles["body"])],
        [Paragraph("공통 사실 경계", styles["small"]), Paragraph("환경 3 · 구현 모듈 15 · Terraform 10/10 · 에이전트 24/24 · 운영 증적은 별도", styles["body"])],
    ]
    table = Table(rows, colWidths=[31 * mm, 117 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def contents_story(strategy, styles):
    accent = colors.HexColor(strategy["accent"])
    flowables = [
        Paragraph("DOCUMENT MAP", styles["kicker"]),
        Paragraph("상세목차와 읽기 방향", styles["h1"]),
        Paragraph(
            f"이 구성은 <b>{escape(strategy['voice'])}</b>을 기준으로 독자의 질문 순서를 다시 설계합니다. 모든 세부 항목을 먼저 보여주고, 본문은 이 흐름을 따라 전개합니다.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
    ]
    rows = []
    for index, (title, subs) in enumerate(strategy["toc"], 1):
        number = Paragraph(f'<font color="{strategy["accent"]}" size="15">{index:02d}</font>', styles["center"])
        entry = Paragraph(
            f"<b>{escape(title)}</b><br/><font color=\"#5C6975\">{' · '.join(escape(item) for item in subs)}</font>",
            styles["toc"],
        )
        page_number = Paragraph(str(min(index + 2, 5)), styles["center"])
        rows.append([number, entry, page_number])
    table = Table(rows, colWidths=[17 * mm, 119 * mm, 12 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.65, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flowables.extend([
        table,
        Spacer(1, 8 * mm),
        Paragraph("이 시안에서 달라지는 것", styles["h2"]),
        Paragraph(
            "장 제목만 바꾸지 않습니다. 문서를 여는 질문, 사실을 소개하는 순서, 대안과 위험을 배치하는 위치, 마지막에 독자에게 남기는 판단 기준까지 이 구성의 목적에 맞게 바꿉니다.",
            styles["body"],
        ),
        PageBreak(),
    ])
    return flowables


def section_table(sections, strategy, styles):
    accent = colors.HexColor(strategy["accent"])
    rows = []
    for index, (heading, body) in enumerate(sections, 1):
        marker = Paragraph(f'<font color="{strategy["accent"]}" size="12">{index:02d}</font>', styles["center"])
        content = Paragraph(f"<b>{escape(heading)}</b><br/>{escape(body)}", styles["body"])
        rows.append([marker, content])
    table = Table(rows, colWidths=[17 * mm, 131 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F5F7")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.65, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (1, 0), (1, -1), 2.2, accent),
    ]))
    return table


def body_page_story(page, strategy, styles):
    return [
        Paragraph(escape(page["kicker"]), styles["kicker"]),
        Paragraph(escape(page["title"]), styles["h1"]),
        Paragraph(f"<b>이 페이지가 답하는 질문</b><br/>{escape(page['question'])}", styles["question"]),
        Paragraph(escape(page["lead"]), styles["body"]),
        Spacer(1, 3 * mm),
        section_table(page["sections"], strategy, styles),
        Spacer(1, 7 * mm),
        Paragraph("읽기 포인트", styles["h2"]),
        Paragraph(
            f"이 내용은 <b>{escape(strategy['name'])}</b>의 관점으로 재배열되었습니다. 같은 구현 사실이라도 독자가 먼저 판단해야 할 질문을 기준으로 근거의 위치와 결론을 달리합니다.",
            styles["body"],
        ),
        PageBreak(),
    ]


def evidence_table(strategy, styles):
    rows = [[
        Paragraph("표현", styles["small"]),
        Paragraph("실제 의미", styles["small"]),
        Paragraph("해석 제한", styles["small"]),
    ]]
    for label, meaning, limit in COMMON_FACTS:
        rows.append([
            Paragraph(f"<b>{escape(label)}</b>", styles["metric"]),
            Paragraph(escape(meaning), styles["metric"]),
            Paragraph(escape(limit), styles["metric"]),
        ])
    table = Table(rows, colWidths=[30 * mm, 74 * mm, 44 * mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F5")),
        ("GRID", (0, 0), (-1, -1), 0.55, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def closing_story(strategy, styles):
    accent = colors.HexColor(strategy["accent"])
    note = Table(
        [[Paragraph(f"<b>이 형식의 장점과 trade-off</b><br/>{escape(strategy['closing_note'])}", styles["body"])]],
        colWidths=[148 * mm], hAlign="LEFT",
    )
    note.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F5F7")),
        ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return [
        Paragraph("CONCLUSION AND EVIDENCE BOUNDARY", styles["kicker"]),
        Paragraph(escape(strategy["closing_title"]), styles["h1"]),
        note,
        Spacer(1, 7 * mm),
        Paragraph("공통 숫자 상세 해설", styles["h2"]),
        Paragraph(
            "10개 구성안을 정확히 비교할 수 있도록 아래 사실 경계는 모두 동일하게 유지합니다. 표현 방식은 달라도 분모와 해석 제한은 바뀌지 않습니다.",
            styles["body"],
        ),
        evidence_table(strategy, styles),
        Spacer(1, 6 * mm),
        Paragraph(
            "최종 포트폴리오에서는 선택한 구성의 상세목차를 PDF 본문과 북마크 패널에 모두 제공하고, 각 수치 바로 옆에 산정 기준·검증 범위·미검증 항목을 함께 표기합니다.",
            styles["small"],
        ),
    ]


def build_sample(strategy):
    styles = styles_for(strategy)
    story = []
    story.extend(cover_story(strategy, styles))
    story.extend(contents_story(strategy, styles))
    for page in strategy["pages"]:
        story.extend(body_page_story(page, strategy, styles))
    story.extend(closing_story(strategy, styles))
    output = OUTPUT_DIR / f"{strategy['slug']}.pdf"
    document = StrategyDocTemplate(str(output), strategy)
    document.build(story)
    return output


def main():
    register_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for strategy in STRATEGIES:
        print(build_sample(strategy))


if __name__ == "__main__":
    main()
