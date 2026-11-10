targetScope = 'resourceGroup'

// Isolated #249 Python/Linux classic Consumption Y1 canary, NO existing Flex modification.
@allowed(['centralindia'])
param location string = 'centralindia'
@allowed(['dev'])
param environmentName string = 'dev'
param storageAccountName string = 'rgaid4e5ddbdf0d21d96'
param functionAppName string = 'rgai-dev-y1-p0249-d4e5ddbd'
param functionPlanName string = 'rgai-dev-y1-p0249'

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource canaryPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: functionPlanName
  location: location
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
    size: 'Y1'
    family: 'Y'
    capacity: 0
  }
  properties: {
    reserved: true
    computeMode: 'Dynamic'
  }
  tags: {
    app: 'RetailGrowthAI'
    environment: environmentName
    purpose: 'p0249-http-ingress-isolation'
  }
}

var storageConnection = format('DefaultEndpointsProtocol=https;AccountName={0};AccountKey={1};EndpointSuffix={2}', storage.name, storage.listKeys().keys[0].value, environment().suffixes.storage)

resource canaryApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  tags: {
    app: 'RetailGrowthAI'
    environment: environmentName
    purpose: 'p0249-http-ingress-isolation'
  }
  properties: {
    reserved: true
    httpsOnly: true
    clientAffinityEnabled: false
    serverFarmId: canaryPlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      alwaysOn: false
      appSettings: [
        { name: 'AzureWebJobsStorage', value: storageConnection }
        { name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING', value: storageConnection }
        { name: 'WEBSITE_CONTENTSHARE', value: toLower(functionAppName) }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'ENABLE_ORYX_BUILD', value: 'true' }
        { name: 'RETAIL_P0249_CANARY_ONLY', value: 'true' }
      ]
    }
  }
}

output canaryFunctionName string = canaryApp.name
output canaryPlanName string = canaryPlan.name
