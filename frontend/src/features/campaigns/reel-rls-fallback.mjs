// Existing-DEV tenant-JWT RLS-only read fallback when Azure Functions HTTP
// ingress returns a pre-handler 503. No customer write, no service_role key,
// no guessed object path, no public storage and no OAuth/session bypass.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const BUCKET='retailgrowth-media'

function validUuid(value) {
  if (typeof value!=='string' || !UUID.test(value)) throw new Error('Invalid resource ID')
  return value
}
function unavailable() {
  const error=new Error('Private video status is temporarily unavailable. Please retry.')
  error.status=503
  return error
}
function absent() {
  const error=new Error('Video not found in this business.')
  error.status=404
  return error
}
function validateOrigin(origin) {
  const url=new URL(origin)
  if (url.protocol!=='https:' || url.username || url.password || url.search ||
      url.hash || !['','/'].includes(url.pathname)) {
    throw new Error('Private media fallback requires a trusted HTTPS Supabase origin')
  }
  return url.origin
}
export function createRenderReadFallback({supabaseOrigin='',publishableKey='',tokenProvider,
  fetchImpl=fetch}={}) {
  if (!supabaseOrigin || !publishableKey) return null
  const origin=validateOrigin(supabaseOrigin)
  if (typeof publishableKey!=='string' || !publishableKey.startsWith('sb_publishable_') ||
      typeof tokenProvider!=='function') throw new Error('Publishable Supabase JWT client required')
  async function read(method,path,token,body) {
    const controller=new AbortController()
    const timer=setTimeout(()=>controller.abort(),12000)
    try {
      const response=await fetchImpl(origin+path,{
        method,redirect:'error',cache:'no-store',signal:controller.signal,
        headers:{apikey:publishableKey,Authorization:'Bearer '+token,
          ...(body===undefined?{}:{'Content-Type':'application/json'})},
        ...(body===undefined?{}:{body:JSON.stringify(body)}),
      })
      if (!response.ok) {
        if (response.status===401) {
          const error=new Error('Session expired. Please sign in again from Account.')
          error.status=401
          throw error
        }
        throw unavailable()
      }
      return await response.json().catch(()=>{throw unavailable()})
    } catch(error) {
      if (error?.status===401) throw error
      throw unavailable()
    } finally { clearTimeout(timer) }
  }
  async function loadJob(jobId,token) {
    const target=validUuid(jobId)
    const query=new URLSearchParams({
      select:'id,shop_id,status,output_asset_id,error_code',
      id:'eq.'+target,limit:'2',
    })
    const jobs=await read('GET','/rest/v1/render_jobs?'+query,token)
    if (!Array.isArray(jobs) || jobs.length>1) throw unavailable()
    if (jobs.length===0) throw absent()
    const row=jobs[0]
    if (!row || row.id!==target || !UUID.test(row.shop_id) ||
        !['QUEUED','RUNNING','FAILED','SUCCEEDED'].includes(row.status)) throw unavailable()
    return row
  }
  async function getRenderJob(jobId) {
    const token=await tokenProvider()
    if (typeof token!=='string' || !token) throw unavailable()
    const row=await loadJob(jobId,token)
    return {job_id:row.id,status:row.status,
      output_asset_id:row.output_asset_id,error_code:row.error_code}
  }
  async function getDownload(jobId) {
    const token=await tokenProvider()
    if (typeof token!=='string' || !token) throw unavailable()
    const job=await loadJob(jobId,token)
    if (job.status!=='SUCCEEDED' || !job.output_asset_id) {
      const error=new Error('Video output is not ready')
      error.status=409
      throw error
    }
    const output=validUuid(job.output_asset_id)
    const query=new URLSearchParams({
      select:'id,shop_id,storage_bucket,mime_type,object_path',
      id:'eq.'+output,shop_id:'eq.'+job.shop_id,limit:'2',
    })
    const assets=await read('GET','/rest/v1/media_assets?'+query,token)
    if (!Array.isArray(assets) || assets.length>1) throw unavailable()
    if (assets.length!==1) throw absent()
    const asset=assets[0]
    if (asset.id!==output || asset.shop_id!==job.shop_id ||
        asset.mime_type!=='video/mp4' || asset.storage_bucket!==BUCKET ||
        typeof asset.object_path!=='string' ||
        !(asset.object_path.startsWith(job.shop_id+'/renders/'+job.id+'/') ||
          asset.object_path===job.shop_id+'/renders/'+job.id+'.mp4') ||
        !asset.object_path.endsWith('.mp4') ||
        asset.object_path.split('/').some(part=>part===''||part==='.'||part==='..') ||
        !/^[a-zA-Z0-9_./-]+$/.test(asset.object_path)) throw unavailable()
    const parts=asset.object_path.split('/').map(encodeURIComponent).join('/')
    // Supabase Storage SELECT RLS checks the user's actual shop membership.
    // This is a signing request only, never creates/updates customer media.
    const signed=await read('POST','/storage/v1/object/sign/'+BUCKET+'/'+parts,
      token,{expiresIn:60})
    if (!signed || typeof signed.signedURL!=='string' ||
        !signed.signedURL.startsWith('/object/sign/'+BUCKET+'/'+asset.object_path+'?token=')) {
      throw unavailable()
    }
    const url=origin+'/storage/v1'+signed.signedURL
    const parsed=new URL(url)
    if (parsed.origin!==origin ||
        !parsed.pathname.startsWith('/storage/v1/object/sign/'+BUCKET+'/'+job.shop_id+'/') ||
        !parsed.searchParams.has('token')) throw unavailable()
    return {url:parsed.toString()}
  }
  return {getRenderJob,getDownload}
}
