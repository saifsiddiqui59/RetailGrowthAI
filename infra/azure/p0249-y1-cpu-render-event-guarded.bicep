// #249 Y1 — EVENT ACTIVATION CANDIDATE ONLY; NEVER deploy from ordinary CI.
// A protected DEV release must first show Flex long-render consumer DISABLED,
// no in-flight duplicate claims, correct SHA-pinned image, immutable roles,
// private media/rights acceptance, and an independently tested rollback.
// Compared with p0249-y1-cpu-render-disabled.bicep this changes the SAME job
// from Manual to queue Event scaling; DO NOT create it as a second consumer.
targetScope = 'resourceGroup'

@allowed(['centralindia'])
param location string = 'centralindia'

@description('Existing dedicated RetailGrowthAI DEV Container Apps environment ID')
param containerAppsEnvironmentId string

@description('Immutable CPU renderer image name@sha256:digest; verify digest in trusted release')
param immutableCpuImage string

@description('Validated RetailGrowthAI DEV queue storage ACCOUNT NAME; must match RETAIL_STORAGE')
param queueStorageAccountName string

@secure()
param retailStorageConnection string

@secure()
param retailSupabaseServiceKey string

@allowed(['VERIFIED_FLEX_RENDER_CONSUMER_DISABLED'])
@description('Supplied only by protected release AFTER independently observed original Flex render consumer shutdown')
param verifiedSingleOwnerHandoff string

@description('MUST reference the same disabled DEV job, not start an additional worker')
param jobName string = 'rgai-dev-y1-cpu-render-disabled'

resource cpuRender 'Microsoft.App/jobs@2026-01-01' = {
  name: jobName
  location: location
  tags: {
    app: 'RetailGrowthAI'
    environment: 'dev'
    issue: '249'
    activation: 'protected-event-cutover'
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    configuration: {
      triggerType: 'Event'
      replicaTimeout: 1800
      replicaRetryLimit: 0
      eventTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
        scale: {
          minExecutions: 0
          maxExecutions: 1
          pollingInterval: 60
          rules: [
            {
              name: 'retail-reel-render'
              type: 'azure-queue'
              metadata: {
                accountName: queueStorageAccountName
                queueName: 'retail-reel-render'
                queueLength: '1'
              }
              auth: [
                {
                  triggerParameter: 'connection'
                  secretRef: 'retail-storage'
                }
              ]
            }
          ]
        }
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
            { name: 'RGAI_CPU_RENDER_SINGLE_OWNER_ACTIVATED', value: verifiedSingleOwnerHandoff }
          ]
        }
      ]
    }
  }
}

// Source only. No secret outputs; no Azure mutation, auto deployment or GPU.
