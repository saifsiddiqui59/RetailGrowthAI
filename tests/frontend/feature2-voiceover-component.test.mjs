import test from 'node:test'
import assert from 'node:assert/strict'
import {execFileSync} from 'node:child_process'
import {resolve} from 'node:path'
test('unmounted voice selector JSX must compile with the exact production Vite engine',()=>{
 const frontend=resolve(import.meta.dirname,'../../frontend')
 const result=execFileSync(process.execPath,['scripts/feature2-voiceover-compile.mjs'],{
  cwd:frontend,encoding:'utf8',timeout:25000
 })
 assert.match(result,/voiceover JSX compiled successfully/)
})
