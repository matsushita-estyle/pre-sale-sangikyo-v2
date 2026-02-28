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
