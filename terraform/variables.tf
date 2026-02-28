variable "project_name" {
  description = "プロジェクト名（リソース名のプレフィックス）"
  type        = string
  default     = "sangikyo-v2"
}

variable "resource_group_name" {
  description = "リソースグループ名"
  type        = string
  default     = "rg_matsushita"
}

variable "location" {
  description = "Azureリージョン"
  type        = string
  default     = "japaneast"
}

variable "tags" {
  description = "リソースに付与するタグ"
  type        = map(string)
  default = {
    Environment = "Development"
    Project     = "Sangikyo-V2"
    ManagedBy   = "Terraform"
  }
}
