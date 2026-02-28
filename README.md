# Pre-Sale Sangikyo V2

営業支援AIエージェント - Azure デプロイバージョン

## アーキテクチャ

- **フロントエンド**: Next.js + TypeScript (Azure Static Web Apps)
- **バックエンド**: FastAPI (Azure App Service B1)
- **インフラ**: Terraform
- **CI/CD**: GitHub Actions

## ディレクトリ構成

```
pre-sale-sangikyo-v2/
├── frontend/           # Next.js アプリ
├── backend/            # FastAPI アプリ
├── terraform/          # Azure インフラ定義
├── .github/workflows/  # CI/CD
└── docs/              # ドキュメント
```

## デプロイ

```bash
# Terraformでインフラ構築
cd terraform
terraform init
terraform plan
terraform apply

# GitHub Actionsで自動デプロイ
git push origin main
```

## 料金

- フロントエンド (Static Web Apps Free): $0/月
- バックエンド (App Service B1): $13/月
- **合計**: 約$13-15/月
