import { useEffect, useRef, useState } from 'react'
import { drawPoster, POSTER_SIZES, POSTER_TEMPLATES } from './poster-canvas.mjs'
import './PosterStudio.css'

const MAX_BYTES = 25 * 1024 * 1024
const SUPPORTED = new Set(['image/jpeg', 'image/png', 'image/webp'])

export default function PosterStudio({ day, businessName = 'Your business' }) {
  const canvas = useRef(null)
  const [brand, setBrand] = useState(businessName || 'Your business')
  const [template, setTemplate] = useState('editorial')
  const [size, setSize] = useState('square')
  const [accent, setAccent] = useState('#B96349')
  const [background, setBackground] = useState('#F6F0E8')
  const [offer, setOffer] = useState('')
  const [photoFile, setPhotoFile] = useState(null)
  const [photo, setPhoto] = useState(null)
  const [rights, setRights] = useState(false)
  const [error, setError] = useState('')
  const [downloadError, setDownloadError] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setBrand(businessName || 'Your business')
  }, [businessName])
  useEffect(() => {
    // Offers cannot silently carry over from a different campaign day.
    setOffer('')
    setRights(false)
  }, [day.id])
  useEffect(() => {
    if (!photoFile) { setPhoto(null); return }
    let active = true
    const url = URL.createObjectURL(photoFile)
    const image = new Image()
    image.onload = () => {
      URL.revokeObjectURL(url)
      if (!active) return
      if (!image.width || !image.height || image.width > 8192 ||
          image.height > 8192 || image.width * image.height > 24_000_000) {
        setPhoto(null)
        setError('Photo dimensions must be within 8,192 pixels per side and 24 megapixels.')
      } else {
        setPhoto(image)
        setError('')
      }
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      if (active) { setPhoto(null); setError('Could not decode this image. Try a standard JPG, PNG or WebP.') }
    }
    image.src = url
    return () => { active = false; URL.revokeObjectURL(url) }
  }, [photoFile])

  useEffect(() => {
    if (!canvas.current) return
    try {
      drawPoster(canvas.current, photo, day,
        { template, size, brand, accent, background, offer })
      setReady(true)
      setDownloadError('')
    } catch (problem) {
      setReady(false)
      setDownloadError(problem.message)
    }
  }, [photo, day, template, size, brand, accent, background, offer])

  function chooseFile(event) {
    const file = event.target.files?.[0] || null
    setRights(false)
    setPhoto(null)
    setPhotoFile(null)
    setError('')
    if (!file) return
    if (!SUPPORTED.has(file.type) || file.size <= 0 || file.size > MAX_BYTES) {
      setError('Use a JPG, PNG or WebP image up to 25 MB. HEIC and animated files are not supported.')
      return
    }
    setPhotoFile(file)
  }

  function download() {
    if (!photo || !rights || !ready || !canvas.current) return
    const name = 'retailgrowth-day-' + day.day_index + '-' + template + '-' + size + '.png'
    canvas.current.toBlob(blob => {
      if (!blob) { setDownloadError('Could not export PNG in this browser.'); return }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = name
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    }, 'image/png')
  }

  return (
    <section className="rg-creative rg-panel" aria-labelledby="rg-creative-title">
      <div className="rg-inline-title">
        <div><span className="rg-kicker">05 / PROMOTIONAL POSTER</span>
          <h2 id="rg-creative-title">Your brand, ready to share.</h2>
          <p>Compose a promotional graphic from today's campaign draft and your own product photo.</p>
        </div>
        <span className="rg-mini-pill">PNG · Preview</span>
      </div>
      <div className="rg-creative-grid">
        <div className="rg-creative-controls">
          <label className="rg-field">
            <span>Business name</span>
            <input aria-label="Poster business name" value={brand}
              maxLength={70} onChange={event => setBrand(event.target.value)} />
          </label>
          <label className="rg-field">
            <span>Product photo (JPG, PNG or WebP)</span>
            <input aria-label="Poster product photo" type="file"
              accept="image/jpeg,image/png,image/webp" onChange={chooseFile} />
          </label>
          {error && <p role="alert" className="rg-validation">{error}</p>}
          <div className="rg-creative-pairs">
            <label className="rg-field"><span>Layout</span>
              <select aria-label="Poster template" value={template}
                onChange={event => setTemplate(event.target.value)}>
                {POSTER_TEMPLATES.map(value => <option key={value} value={value}>
                  {value[0].toUpperCase() + value.slice(1)}</option>)}
              </select>
            </label>
            <label className="rg-field"><span>Format</span>
              <select aria-label="Poster size" value={size}
                onChange={event => setSize(event.target.value)}>
                <option value="square">Square · 1080 × 1080</option>
                <option value="portrait">Portrait · 1080 × 1350</option>
              </select>
            </label>
          </div>
          <div className="rg-creative-pairs">
            <label className="rg-field"><span>Accent</span>
              <input aria-label="Poster accent color" type="color" value={accent}
                onChange={event => setAccent(event.target.value)} />
            </label>
            <label className="rg-field"><span>Background</span>
              <input aria-label="Poster background color" type="color" value={background}
                onChange={event => setBackground(event.target.value)} />
            </label>
          </div>
          <label className="rg-field"><span>Approved offer (optional)</span>
            <input aria-label="Poster offer" value={offer} maxLength={110}
              onChange={event => setOffer(event.target.value)}
              placeholder="e.g. 20% off through Nov 14" />
            <small>Enter only genuine, approved offers; no offer is invented by the app.</small>
          </label>
          <label className="rg-creative-consent">
            <input type="checkbox" checked={rights} onChange={event => setRights(event.target.checked)} />
            <span>I confirm I have the commercial rights to use this product image.</span>
          </label>
          <button type="button" className="rg-button rg-primary"
            disabled={!ready || !photo || !rights} onClick={download}>
            Download generated PNG
          </button>
          {downloadError && <p className="rg-validation" role="alert">{downloadError}</p>}
          <p className="rg-subtle">This is a real browser-generated PNG, not a hosted render. Your selected file stays on this device; the design is not saved to your account and is not published.</p>
        </div>
        <div className="rg-creative-preview">
          <canvas ref={canvas} className="rg-creative-canvas" role="img"
            aria-label={'Live ' + template + ' poster preview for campaign day ' + day.day_index} />
          <p className="rg-subtle">{POSTER_SIZES[size].join(' × ')} pixels · Day {day.day_index} · {photo ? 'Your photo' : 'Add your photo for export'}</p>
        </div>
      </div>
    </section>
  )
}
