terraform {
  required_version = ">= 1.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true  # Skip automatic registration
}

# リソースグループ
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

# App Service Plan (B1)
resource "azurerm_service_plan" "backend" {
  name                = "${var.project_name}-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"

  tags = var.tags
}

# App Service (Backend - FastAPI)
resource "azurerm_linux_web_app" "backend" {
  name                = "${var.project_name}-backend"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.backend.id

  site_config {
    application_stack {
      python_version = "3.11"
    }

    # CORS設定
    cors {
      allowed_origins = ["*"]
      support_credentials = false
    }

    # タイムアウト延長
    # always_on = false  # B1プランではfalse
  }

  app_settings = {
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "ENABLE_ORYX_BUILD"              = "true"
    "WEBSITES_PORT"                  = "8000"
  }

  https_only = true

  tags = var.tags
}

# Static Web App (Frontend - Next.js)
resource "azurerm_static_web_app" "frontend" {
  name                = "${var.project_name}-frontend"
  location            = "eastasia"  # Static Web Appsの利用可能リージョン
  resource_group_name = azurerm_resource_group.main.name
  sku_tier            = "Free"
  sku_size            = "Free"

  tags = var.tags
}

# Cosmos DB アカウント
resource "azurerm_cosmosdb_account" "main" {
  name                = "${var.project_name}-cosmosdb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  enable_automatic_failover = false
  enable_free_tier          = false  # 無料枠は既に別アカウントで使用中

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"  # サーバーレスモード
  }

  tags = var.tags
}

# Cosmos DB データベース
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "SangikyoDB"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Users コンテナ
resource "azurerm_cosmosdb_sql_container" "users" {
  name                = "Users"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/user_id"
}

# Customers コンテナ
resource "azurerm_cosmosdb_sql_container" "customers" {
  name                = "Customers"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/customer_id"
}

# Products コンテナ
resource "azurerm_cosmosdb_sql_container" "products" {
  name                = "Products"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/product_id"
}

# Deals コンテナ
resource "azurerm_cosmosdb_sql_container" "deals" {
  name                = "Deals"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/deal_id"
}

# News コンテナ
resource "azurerm_cosmosdb_sql_container" "news" {
  name                = "News"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_path  = "/news_id"
}
