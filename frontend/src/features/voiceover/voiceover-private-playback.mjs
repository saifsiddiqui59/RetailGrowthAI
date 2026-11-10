// Browser-side last-mile validation of a trusted, short-lived private audio read.
// The server MUST independently enforce current JWT, OWNER/EDITOR rights,
// revocation and original media SHA; browser digests are not authorization.
const SHA = /^[a-f0-9]{64}$/
const isBytes = value => value instanceof ArrayBuffer || value instanceof Uint8Array
export async function verifyLocalPrivatePlayback({shopId,campaignId,receipt,readResult}) {
  if (!receipt || !readResult || !shopId || !campaignId ||
      receipt.shop_id!==shopId || receipt.campaign_id!==campaignId ||
      readResult.shop_id!==shopId || readResult.campaign_id!==campaignId ||
      receipt.private!==true || readResult.private!==true ||
      receipt.provider!=='kokoro-onnx' || receipt.can_publish!==false ||
      typeof receipt.private_audio_asset_id!=='string' ||
      readResult.asset_id!==receipt.private_audio_asset_id ||
      !SHA.test(receipt.original_audio_sha256??'') ||
      readResult.original_audio_sha256!==receipt.original_audio_sha256 ||
      readResult.mime_type!=='audio/wav' || !isBytes(readResult.audio_bytes)) {
    throw new Error('Private Kokoro audio binding is not verified')
  }
  const bytes=new Uint8Array(readResult.audio_bytes)
  if (bytes.length<128 || bytes.length>20_000_000) {
    throw new Error('Private WAV length invalid')
  }
  const ascii=(from,len)=>String.fromCharCode(...bytes.slice(from,from+len))
  if (ascii(0,4)!=='RIFF' || ascii(8,4)!=='WAVE') {
    throw new Error('Private audio is not original WAV')
  }
  if (!globalThis.crypto?.subtle) {
    throw new Error('Secure browser audio digest unavailable')
  }
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)))
    .map(n=>n.toString(16).padStart(2,'0')).join('')
  if (digest!==receipt.original_audio_sha256) {
    throw new Error('Private audio SHA-256 mismatch')
  }
  return {bytes,mime_type:'audio/wav',sha256:digest}
}
