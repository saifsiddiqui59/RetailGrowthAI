targetScope = 'resourceGroup'

@description('RetailGrowthAI DEV only.')
@allowed(['dev'])
param environmentName string = 'dev'

@description('Confirm Flex Consumption region availability before approved deployment.')
@allowed(['centralindia'])
param location string = 'centralindia'

@description('New dedicated StorageV2 globally unique lowercase name.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('New RetailGrowthAI DEV Function App name.')
param functionAppName string

@description('New Flex Consumption hosting plan name.')
param functionPlanName string

@description('Exact HTTPS frontend origin, never wildcard.')
param frontendOrigin string

@description('DEV cap applies to EACH independently scaling function group; higher values require a review.')
@allowed([1, 2])
param maxInstances int = 1

@description('DEV is capped to 2048 MiB pending representative render measurements.')
@allowed([2048])
param instanceMemoryMB int = 2048

var deploymentContainerName = 'retailgrowth-functions-packages'
var planningQueueName = 'retail-campaign-planning'
var renderingQueueName = 'retail-reel-render'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  tags: { app: 'RetailGrowthAI', environment: environmentName }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true // Current Python QueueClient.from_connection_string requires this.
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: storage
}

resource packageContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: deploymentContainerName
  parent: blobService
  properties: { publicAccess: 'None' }
}

resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-05-01' = {
  name: 'default'
  parent: storage
}

resource planningQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: planningQueueName
  parent: queueService
}

resource renderingQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: renderingQueueName
  parent: queueService
}

resource flexPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: functionPlanName
  location: location
  kind: 'functionapp'
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: { reserved: true }
  tags: { app: 'RetailGrowthAI', environment: environmentName }
}

// Backend secrets are intentionally NOT template parameters or outputs.
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
          value: format('{0}{1}', storage.properties.primaryEndpoints.blob, packageContainer.name)
          authentication: {
            type: 'StorageAccountConnectionString'
            storageAccountConnectionStringName: 'AzureWebJobsStorage'
          }
        }
      }
      runtime: { name: 'python', version: '3.12' }
      scaleAndConcurrency: {
        instanceMemoryMB: instanceMemoryMB
        maximumInstanceCount: maxInstances
      }
    }
  }
  dependsOn: [packageContainer, planningQueue, renderingQueue]
}

output functionAppResourceId string = functionApp.id
output planningQueueName string = planningQueue.name
output renderingQueueName string = renderingQueue.name
