#!/usr/bin/env node
// Private, backend-only render adapter; never expose as user HTML endpoint.
import { readFile, stat } from 'node:fs/promises'
import { resolve, join } from 'node:path'
import { spawnSync } from 'node:child_process'
import { createRenderJob, executeRenderJob } from '@hyperframes/producer'

async function main() {
  const [projectArg, outputArg] = process.argv.slice(2)
  if (!projectArg || !outputArg) throw Error('Usage: render.mjs <compiled-project> <output.mp4>')
  const project = resolve(projectArg)
  const output = resolve(outputArg)
  if (!output.endsWith('.mp4') || output.startsWith(project + '/')) {
    throw Error('Output must be MP4 outside compiled project')
  }
  const config = JSON.parse(await readFile(join(project, 'render-config.json'), 'utf8'))
  if (config.contract_version !== 'rg_video_v2' || config.renderer !== 'hyperframes' ||
      ![15, 30, 60].includes(config.duration_seconds) || ![24, 30].includes(config.fps) ||
      ![[540, 960], [1080, 1920]].some(([w, h]) => config.width === w && config.height === h) ||
      config.format !== 'mp4' || config.quality !== 'standard') {
    throw Error('Unapproved composition config')
  }
  const html = await readFile(join(project, 'index.html'), 'utf8')
  if (!html.includes('data-composition-id="main"') || !html.includes('data-no-timeline') ||
      /<script\b|<iframe\b|(?:src|href)\s*=\s*["']\s*(?:https?:|javascript:)|@import\b|onerror\s*=|onload\s*=/i.test(html)) {
    throw Error('Untrusted composition markup')
  }
  if ((await stat(project)).isSymbolicLink()) throw Error('Symlink project forbidden')
  const job = createRenderJob({ fps: config.fps, quality: 'standard', format: 'mp4' })
  await executeRenderJob(job, project, output, currentJob => {
    if (typeof currentJob?.progress === 'number') {
      process.stderr.write('render progress ' + Math.round(currentJob.progress) + '%\n')
    }
  })
  const probe = spawnSync('ffprobe', ['-v', 'error', '-show_streams', '-show_format',
    '-of', 'json', output], { encoding: 'utf8', timeout: 20000 })
  if (probe.status !== 0) throw Error('Output ffprobe failed')
  const info = JSON.parse(probe.stdout)
  const video = info.streams.filter(s => s.codec_type === 'video')
  const audio = info.streams.filter(s => s.codec_type === 'audio')
  const seconds = Number(info.format.duration)
  const fpsParts = String(video[0]?.avg_frame_rate ?? '').split('/')
  const measuredFps = fpsParts.length === 2
    ? Number(fpsParts[0]) / Number(fpsParts[1]) : NaN
  if (video.length !== 1 || audio.length !== 1 ||
      video[0].codec_name !== 'h264' || audio[0].codec_name !== 'aac' ||
      video[0].width !== config.width || video[0].height !== config.height ||
      video[0].pix_fmt !== 'yuv420p' ||
      !Number.isFinite(measuredFps) || Math.abs(measuredFps - config.fps) > .1 ||
      !Number.isFinite(seconds) || Math.abs(seconds - config.duration_seconds) > .3) {
    throw Error('Output invalid: duration, streams, codec, pixel format, exact resolution or fps')
  }
  process.stdout.write(JSON.stringify({ status: 'VALIDATED', duration: seconds,
    width: video[0].width, height: video[0].height, fps: config.fps, output }) + '\n')
}
main().catch(err => {
  process.stderr.write('FEATURE4 RENDER FAILED: ' + err.message + '\n')
  process.exitCode = 2
})
