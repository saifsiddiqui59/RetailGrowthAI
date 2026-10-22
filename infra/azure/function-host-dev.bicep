targetScope = 'resourceGroup'

@allowed(['centralindia'])
param location string = 'centralindia'

@allowed(['dev'])
param environmentName string = 'dev'

@description('Existing verified, dedicated RetailGrowthAI DEV StorageV2 account.')
param storageAccountName string

@description('DEV Flex consumption Function App, globally unique.')
param functionAppName string

@description('DEV single purpose Flex plan.')
param functionPlanName string = 'rgai-dev-flex'

@description('Existing verified HTTPS Azure Static Web App origin.')
param frontendOrigin string = 'https://purple-dune-06b5da200.2.azurestaticapps.net'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  name: 'default'
  parent: storage
}
resource privatePackages 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' existing = {
  name: 'retailgrowth-functions-packages'
  parent: blobService
}

resource flexPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: functionPlanName
  location: location
  kind: 'functionapp'
  sku: { name: 'FC1', tier: 'FlexConsumption' }
  properties: { reserved: true }
  tags: { app: 'RetailGrowthAI', environment: environmentName }
}

var storageConnection = format('DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1};EndpointSuffix={2}', storage.name, storage.listKeys().keys[0].value, environment().suffixes.storage)

resource functionApp 'Microsoft.Web/sites@2024-11-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  tags: { app: 'RetailGrowthAI', environment: environmentName }
  properties: {
    serverFarmId: flexPlan.id
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      cors: {
        allowedOrigins: [frontendOrigin]
        supportCredentials: false
      }
      appSettings: [
        { name: 'AzureWebJobsStorage', value: storageConnection }
        { name: 'RETAIL_STORAGE', value: storageConnection }
        { name: 'RETAIL_ENABLE_MOCK_CAMPAIGNS', value: 'false' }
      ]
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: format('{0}{1}', storage.properties.primaryEndpoints.blob, privatePackages.name)
          authentication: {
            type: 'StorageAccountConnectionString'
            storageAccountConnectionStringName: 'AzureWebJobsStorage'
          }
        }
      }
      runtime: { name: 'python', version: '3.12' }
      scaleAndConcurrency: {
        instanceMemoryMB: 2048
        maximumInstanceCount: 1
      }
    }
  }
}
output devFunctionName string = functionApp.name
output devFunctionResourceId string = functionApp.id
