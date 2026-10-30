import { memo } from 'react'
// Timeline Studio's WaveformStrip had deep model/audio-canvas dependencies.
// Feature4 only renders a static preview of already authorized metadata;
// it does not synthesize audio or present a fake waveform.
export const WaveformStrip = memo(function WaveformStrip({ peaks }) {
  return <div className="f4-vendor-waveform" aria-hidden="true">{Array.isArray(peaks) && peaks.length
    ? peaks.slice(0, 48).map((n, i) => <i key={i} style={{ height: (Math.max(0.08, Math.min(1, Number(n) || 0)) * 100) + '%' }} />)
    : <span>Audio analysis unavailable</span>}</div>
})
