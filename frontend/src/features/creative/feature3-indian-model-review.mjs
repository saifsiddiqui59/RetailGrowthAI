/** Feature #3: audited, immutable SOURCE REVIEW shortlist for Indian-fashion themes.
 * These are synthetic character-generator metadata labels, NOT real persons,
 * verified heritage, fashion fit, commercial image rights or customer approval.
 * No remote fetch/import is performed here. Git blob hashes were independently
 * checked against the exact repository tree at SOURCE_REVISION.
 */
export const SOURCE_REVISION = '231f73aa43b32a38001759944baa01d7d154ce26'
export const SOURCE_REPOSITORY = 'Prompt-Haus/OpenPeople'
export const CANDIDATE_STATUS = 'PENDING_SOURCE_AND_IMAGE_LICENSE_REVIEW'

const catalog = [
  { id: 'P009', age: '18–25', presentation: 'female', profile: '88% Indian, 12% Western Latin American', metadataSha: '182cae68986ef8a42ad21f554ebbb38a1735b400', full: 'c5f3072519fe7818eca529f7be1f33d30d16ad5e', portrait: '882f15e631e1a5b6f698ae9afbb781d69154e4f4' },
  { id: 'P006', age: '35–45', presentation: 'female', profile: '80% South Indian, 20% East African', metadataSha: '000ad8d9e024d8164d02f75c1876da52f64f38ca', full: 'c84d6cb84b50a7cbfb40c3449899f4b8b5c19294', portrait: 'f6bcb8edf8b25ba0e32dee57e0d4feb6e35a8e25' },
  { id: 'P079', age: '25–35', presentation: 'female', profile: '58% Eastern Indian, 42% South Asian', metadataSha: 'e887cdd8cb1c0f834cc62a1c80b2be79f0f6335c', full: '0a73a528e971efbb25e3a4db540d8e52beaa3ba3', portrait: 'e900b302e1b8c98d6edeb2727c01909593e7fdfe' },
  { id: 'P033', age: '18–25', presentation: 'female', profile: '39% Middle Eastern, 61% Indian', metadataSha: 'aec47efd099bd366d0e0a6d8d90c20f92706df75', full: '0206fd10a6a404355bdbfb6e103cabfa27cbe9b8', portrait: '774db25015e0149b2781100bd1632e17d7b752a3' },
  { id: 'P054', age: '45–55', presentation: 'female', profile: '54% Central Indian, 46% Middle Eastern', metadataSha: '89ff26b4c9073ce6be13374be13c310adb3d1257', full: 'cba1ac62784adaf4a36e74e0e4ca9bfcb758e11d', portrait: 'e077734482ebc8a087a5154873d2324208ae112e' },
  { id: 'P059', age: '25–35', presentation: 'male', profile: '81% Indian, 19% American', metadataSha: '022e568318d10967e91bb3c4cd37154a6a299dff', full: '2bb4f9a5eba0fc6625287b7bfcdfaba1ad60e5ba', portrait: '3297950b3e91a1b612d74622df6d24d492ff01c4' },
  { id: 'P025', age: '25–35', presentation: 'male', profile: '12% Hispanic, 88% Central Indian', metadataSha: '06674584533b0cdd0dc4abb34d8053cb500c40bb', full: 'dc3873aa3ed41e2b3a732924e13521ce6c5b3035', portrait: 'addd285e41b2f14a526d8f2ed973dd5403f4eca9' },
  { id: 'P016', age: '25–35', presentation: 'male', profile: '71% East Indian, 29% East Australian', metadataSha: 'badde612f57bb41ef8f9887f400ef821b2fb3e95', full: '7e14b4625cbb6a575f7b124dab0681f267f2a1d9', portrait: 'db7d20829340a7130537b945f30700aa71f5e8d6' },
]

export const INDIAN_MODEL_CANDIDATES = Object.freeze(
  catalog.map(entry => Object.freeze({
    id: entry.id,
    ageRange: entry.age,
    metadataPresentation: entry.presentation,
    metadataDescription: entry.profile,
    metadataGitBlobSha: entry.metadataSha,
    imageGitBlobs: Object.freeze({
      studio_posture: entry.full,
      studio_portrait: entry.portrait,
    }),
    status: CANDIDATE_STATUS,
  })),
)

const IMAGE_KINDS = new Set(['studio_posture', 'studio_portrait'])

export function getIndianModelCandidate(personId) {
  return INDIAN_MODEL_CANDIDATES.find(person => person.id === personId) || null
}

export function indianModelReviewUrl(personId, imageKind = 'studio_posture') {
  if (!IMAGE_KINDS.has(imageKind) || !getIndianModelCandidate(personId)) return null
  return `https://github.com/${SOURCE_REPOSITORY}/blob/${SOURCE_REVISION}/openpeople/data/curated/${personId}/assets/${imageKind}.jpg`
}

export function createIndianModelReviewPacket(personId, imageKind = 'studio_posture') {
  const person = getIndianModelCandidate(personId)
  const sourceUrl = indianModelReviewUrl(personId, imageKind)
  if (!person || !sourceUrl) throw Error('Select a reviewed-source candidate and image kind')
  return {
    schema: 'retailgrowth.model-review-request.v1',
    source_repository: SOURCE_REPOSITORY,
    source_revision: SOURCE_REVISION,
    person_id: person.id,
    image_kind: imageKind,
    image_git_blob_sha: person.imageGitBlobs[imageKind],
    metadata_git_blob_sha: person.metadataGitBlobSha,
    source_url: sourceUrl,
    attribution: 'OpenPeople by Prompt Haus — CC BY 4.0 (source claim; verify)',
    source_license_claim: 'CC-BY-4.0',
    source_profile_description: person.metadataDescription,
    source_profile_is_synthetic: true,
    status: CANDIDATE_STATUS,
    licensed_for_retailgrowth: false,
    rights_evidence_verified: false,
    visual_quality_approved: false,
    commercially_reusable: false,
    saved_to_private_library: false,
    approved: false,
    published: false,
    generation_gpu_calls: 0,
  }
}
