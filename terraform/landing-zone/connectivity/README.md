# Central Connectivity Root

이 root는 서비스 계정과 공통 EKS 환경 root가 만든 attachment를 Network account route table에 연결합니다. attachment ID는 보호된 배포 artifact로 전달하며, 사람이 검토한 CIDR·service·environment registry와 대조합니다.

예시 입력 형태:

```hcl
service_attachments = {
  commerce-prod = {
    attachment_id = "tgw-attach-replace"
    vpc_cidr      = "10.65.0.0/16"
    environment   = "prod"
    service_name  = "commerce"
  }
  platform-prod = {
    attachment_id = "tgw-attach-replace"
    vpc_cidr      = "10.20.0.0/16"
    environment   = "prod"
    service_name  = "cloud-portfolio"
  }
}
```

서비스 간 full mesh는 기본값이 아닙니다. `allowed_routes`를 비워두면 VPC는 TGW에 attached되지만 다른 service CIDR을 자동 학습하지 않습니다.
