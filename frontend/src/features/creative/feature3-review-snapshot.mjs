/** Read-only, bounded offline inspector of JWT-scoped private v2 draft rows.
 * No signed image URLs, remote fetch, review mutation or publication grants.
 * The authenticated API and server RLS remain authoritative.
 */
import {FEATURE3_FORMATS,validateFeature3Design} from './feature3-design.mjs'
import {feature3DraftMediaReady} from './feature3-workspace-scope.mjs'

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const SHA=/^[a-f0-9]{64}$/
const STATUSES=new Set(['DRAFT','APPROVED','REJECTED'])

export function createFeature3ReviewSnapshot(row,{shopId,campaignId,dayId,imageMap={}}={}) {
  if(!row || typeof row!=='object' || Array.isArray(row) ||
     typeof shopId!=='string' || !UUID.test(shopId) ||
     typeof campaignId!=='string' || !UUID.test(campaignId) ||
     typeof dayId!=='string' || !UUID.test(dayId) ||
     row.shop_id!==shopId || row.campaign_id!==campaignId || row.day_id!==dayId ||
     typeof row.id!=='string' || !UUID.test(row.id) ||
     !Number.isSafeInteger(row.revision) || row.revision<1 ||
     !STATUSES.has(row.status) ||
     typeof row.server_document_sha256!=='string' ||
     !SHA.test(row.server_document_sha256)) {
    throw Error('Untrusted tenant-scoped poster review')
  }
  const design=validateFeature3Design(row.design)
  if(design.shop_id!==shopId || !feature3DraftMediaReady(design,imageMap))
    throw Error('Private design or image rights not available')
  const layers=Object.freeze(design.layers.map(layer=>{
    const geometry={id:layer.id,type:layer.type,x:layer.x,y:layer.y,w:layer.w,h:layer.h}
    if(layer.type==='text')return Object.freeze({...geometry,
      text:layer.text,color:layer.color,fontSize:layer.font_size,bold:layer.bold})
    if(layer.type==='rect')return Object.freeze({...geometry,color:layer.color})
    // Never copy original object URLs, URLs in the map, Blob bytes or
    // rendered image source into review metadata.
    return Object.freeze({...geometry,
      mediaLabel:'Private registered asset '+layer.asset_id.slice(0,8)})
  }))
  const dimensions=FEATURE3_FORMATS[design.format]
  return Object.freeze({
    id:row.id,revision:row.revision,status:row.status,
    format:design.format,template:design.template,background:design.background,
    width:dimensions[0],height:dimensions[1],layers,
    publicationApproved:false,commercialRightsVerified:false,
  })
}
