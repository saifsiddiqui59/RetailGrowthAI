targetScope = 'resourceGroup'

// SOURCE ONLY: separate scale-to-zero F4 CPU worker. This file is not a
// deployment authorization. Never reconfigure legacy v1 Flex/Y1 or WineShopPOS.
@allowed(['centralindia'])
param location string = 'centralindia'
@allowed(['dev'])
param environmentName string = 'dev'
@allowed(['rgaid4e5ddbdf0d21d96'])
param storageAccountName string = 'rgaid4e5ddbdf0d21d96'
@allowed(['rgai-dev-f4cpu-d4e5ddbd'])
param functionAppName string = 'rgai-dev-f4cpu-d4e5ddbd'
@allowed(['rgai-dev-f4cpu-plan'])
param functionPlanName string = 'rgai-dev-f4cpu-plan'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}
resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  name: 'default'
  parent: storage
}
resource privatePackages 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: 'retailgrowth-f4cpu-packages'
  parent: blobSvc
  properties: {
    publicAccess: 'None'
  }
}

// Do not reuse the Y1 or the legacy Flex Consumption plan.
resource workerPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: functionPlanName
  location: location
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true
  }
  tags: {
    app: 'RetailGrowthAI'
    environment: environmentName
    purpose: 'feature4-cpu-private-worker'
  }
}

// This connection is produced by the infrastructure provider, never printed
// to CI or placed in the public frontend. App secrets are configured in a
// separate protected release after the resource has been identity verified.
var storageConnection = format(
  'DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1};EndpointSuffix={2}',
  storage.name,
  storage.listKeys().keys[0].value,
  environment().suffixes.storage
)

resource workerApp 'Microsoft.Web/sites@2024-11-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  tags: {
    app: 'RetailGrowthAI'
    environment: environmentName
    purpose: 'feature4-cpu-private-worker'
  }
  properties: {
    serverFarmId: workerPlan.id
    reserved: true
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: storageConnection }
        { name: 'RETAIL_STORAGE', value: storageConnection }
        { name: 'RETAIL_FEATURE4_CPU_WORKER_ENABLED', value: 'false' }
        { name: 'RETAIL_FEATURE4_CPU_RENDER_ENABLED', value: 'false' }
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
      runtime: {
        name: 'python'
        version: '3.11'
      }
      scaleAndConcurrency: {
        instanceMemoryMB: 2048
        maximumInstanceCount: 1
      }
    }
  }
}

output devFeature4WorkerName string = workerApp.name
output devFeature4WorkerResourceId string = workerApp.id
output devFeature4PrivatePackageContainer string = privatePackages.name
