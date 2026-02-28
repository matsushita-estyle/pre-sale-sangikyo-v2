output "resource_group_name" {
  description = "リソースグループ名"
  value       = azurerm_resource_group.main.name
}

output "backend_app_name" {
  description = "バックエンド App Service名"
  value       = azurerm_linux_web_app.backend.name
}

output "backend_url" {
  description = "バックエンドURL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "frontend_app_name" {
  description = "フロントエンド Static Web App名"
  value       = azurerm_static_web_app.frontend.name
}

output "frontend_url" {
  description = "フロントエンドURL"
  value       = "https://${azurerm_static_web_app.frontend.default_host_name}"
}

output "frontend_api_key" {
  description = "Static Web App APIキー（GitHub Actions用）"
  value       = azurerm_static_web_app.frontend.api_key
  sensitive   = true
}

output "backend_publish_profile_command" {
  description = "バックエンドのPublish Profile取得コマンド"
  value       = "az webapp deployment list-publishing-profiles --name ${azurerm_linux_web_app.backend.name} --resource-group ${azurerm_resource_group.main.name} --xml"
}
