// Compile the isolated F2 voiceover React component even before F4 mounts it.
// This is real Vite/esbuild JSX compilation, not a filename/string-only check.
import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {resolve, dirname} from 'node:path'
import {transformWithEsbuild} from 'vite'

const self=dirname(fileURLToPath(import.meta.url))
const file=resolve(self,'../src/features/voiceover/VoiceoverSelector.jsx')
const source=readFileSync(file,'utf8')
const output=await transformWithEsbuild(source,file,{
  loader:'jsx',jsx:'automatic',target:'es2022'
})
if(typeof output.code!=='string'||!output.code.includes('jsx')||
   !output.code.includes('Generate narration')||
   !output.code.includes('Generate preview')||
   !output.code.includes('Upload for private review')) {
  throw Error('Feature2 VoiceoverSelector not compiled with expected actions')
}
process.stdout.write('Feature2 isolated voiceover JSX compiled successfully\n')
