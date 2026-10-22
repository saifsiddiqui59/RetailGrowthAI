targetScope = 'resourceGroup'
@description('Exact RetailGrowthAI DEV Azure Storage account; lowercase globally unique.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@allowed(['dev'])
param environmentName string = 'dev'

@allowed(['centralindia'])
param location string = 'centralindia'

resource account 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  tags: { app: 'RetailGrowthAI', environment: environmentName, purpose: 'functions-queues-private-packages' }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true // Existing Azure Queue SDK/Function contract currently requires Shared Key.
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobSvc 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: 'default'
  parent: account
}
resource privatePackages 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: 'retailgrowth-functions-packages'
  parent: blobSvc
  properties: { publicAccess: 'None' }
}
resource queueSvc 'Microsoft.Storage/storageAccounts/queueServices@2023-05-01' = {
  name: 'default'
  parent: account
}
resource planQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: 'retail-campaign-planning'
  parent: queueSvc
}
resource renderQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: 'retail-reel-render'
  parent: queueSvc
}
resource planPoison 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: 'retail-campaign-planning-poison'
  parent: queueSvc
}
resource renderPoison 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  name: 'retail-reel-render-poison'
  parent: queueSvc
}
output storageName string = account.name
output privateContainerName string = privatePackages.name
output queueNames array = [planQueue.name, renderQueue.name, planPoison.name, renderPoison.name]
