// RetailGrowthAI Issue #249 — SOURCE ONLY, not an authorized deployment.
// Existing dedicated DEV group only. Manual trigger and missing activation
// deliberately prevent ANY queue consumption during initial provisioning.
// A separate reviewed, protected release must migrate to Event trigger ONLY
// after verifying the original Flex render consumer is disabled.
//
// See Microsoft.App/jobs@2026-01-01 and official Container Apps Jobs docs.
targetScope = 'resourceGroup'

@allowed(['centralindia'])
param location string = 'centralindia'

@description('Existing approved dedicated RetailGrowthAI DEV Container Apps environment resource ID. No new environment created.')
param containerAppsEnvironmentId string

@description('Reviewed immutable CPU-only image including digest @sha256:<64 hex>; never a mutable tag.')
param immutableCpuImage string

@secure()
@description('Dedicated RetailGrowthAI DEV Azure Storage queue connection. Must match existing RETAIL_STORAGE in protected runner.')
param retailStorageConnection string

@secure()
@description('Dedicated RetailGrowthAI DEV Supabase service-role key, never a public client value.')
param retailSupabaseServiceKey string

@description('Billed CPU job name, reserved in RetailGrowthAI DEV only.')
param jobName string = 'rgai-dev-y1-cpu-render-disabled'

resource cpuRender 'Microsoft.App/jobs@2026-01-01' = {
  name: jobName
  location: location
  tags: {
    app: 'RetailGrowthAI'
    environment: 'dev'
    issue: '249'
    activation: 'disabled-manual-only'
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      // Manual jobs never scale on queue messages; runtime's activation
      // guard is intentionally NOT supplied to this disabled candidate.
      triggerType: 'Manual'
      replicaTimeout: 1800
      replicaRetryLimit: 0
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      secrets: [
        { name: 'retail-storage', value: retailStorageConnection }
        { name: 'retail-supabase-service', value: retailSupabaseServiceKey }
      ]
    }
    template: {
      containers: [
        {
          name: 'retailgrowth-cpu-render'
          image: immutableCpuImage
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            { name: 'RETAIL_STORAGE', secretRef: 'retail-storage' }
            { name: 'RETAIL_SUPABASE_SERVICE_ROLE_KEY', secretRef: 'retail-supabase-service' }
            { name: 'RETAIL_SUPABASE_URL', value: 'https://jeearzffnjbvghwjjjrf.supabase.co' }
            { name: 'RGAI_CPU_RENDER_HOSTING', value: 'azure-container-apps-job' }
            { name: 'RGAI_CPU_RENDER_RG', value: 'rg-retailgrowth-dev' }
            { name: 'RGAI_CPU_RENDER_QUEUE_NAME', value: 'retail-reel-render' }
            { name: 'RGAI_CPU_RENDER_REPLICA_TIMEOUT_SECONDS', value: '1800' }
            // Deliberately OMIT the real activation marker.
            // cpu_render_job.preflight() must FAIL until an independent
            // release proves Flex render consumer actually disabled.
          ]
        }
      ]
    }
  }
}

// No resource-id, secret or connection-string outputs and no paid GPU.
