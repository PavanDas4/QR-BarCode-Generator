import { useState, useRef } from 'react'
import axios from 'axios'
import Papa from 'papaparse'
import { SketchPicker } from 'react-color'

const initialValues = {
  mode: 'qrcode',
  text: '',
  heading: '',
  description: '',
  foreground: '#000000',
  background: '#ffffff',
  fontSize: 18,
  fontFamily: 'Arial',
  useGradient: false,
  gradientFrom: '#ffffff',
  gradientTo: '#000000',
  bgImage: null,
  logo: null,
  barcodeType: 'code128'
}

function App() {
  const [values, setValues] = useState(initialValues)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [bulkFile, setBulkFile] = useState(null)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const setValue = (field, value) => {
    setValues(prev => ({ ...prev, [field]: value }))
  }

  const handleFileChange = (field, file) => {
    setValue(field, file)
  }

  const validateForm = () => {
    if (!values.text) {
      setError('Enter text for QR/Barcode.')
      return false
    }
    if (!values.heading || values.heading.length > 25) {
      setError('Heading is required and must be ≤ 25 characters.')
      return false
    }
    if (values.description.length > 75) {
      setError('Description must be ≤ 75 characters.')
      return false
    }
    setError('')
    return true
  }

  const handleGenerate = async () => {
    if (!validateForm()) return
    setLoading(true)
    try {
      const formData = new FormData()
      Object.entries(values).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          formData.append(key, value)
        }
      })
      const response = await axios.post('/api/generate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      })
      const url = URL.createObjectURL(new Blob([response.data], { type: 'image/png' }))
      setPreviewUrl(url)
    } catch (err) {
      setError('Failed to generate image.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPreview = () => {
    if (!previewUrl) return
    const link = document.createElement('a')
    link.href = previewUrl
    link.download = `${values.mode}-export.png`
    link.click()
  }

  const handleBulkUpload = async () => {
    if (!bulkFile) {
      setError('Select a CSV file first.')
      return
    }
    setError('')
    setLoading(true)
    const formData = new FormData()
    formData.append('csv', bulkFile)
    formData.append('mode', values.mode)
    formData.append('foreground', values.foreground)
    formData.append('background', values.background)
    formData.append('fontSize', values.fontSize)
    formData.append('fontFamily', values.fontFamily)
    formData.append('useGradient', values.useGradient)
    formData.append('gradientFrom', values.gradientFrom)
    formData.append('gradientTo', values.gradientTo)
    formData.append('barcodeType', values.barcodeType)
    if (values.bgImage) formData.append('bgImage', values.bgImage)
    if (values.logo) formData.append('logo', values.logo)
    try {
      const response = await axios.post('/api/bulk', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      })
      const url = URL.createObjectURL(new Blob([response.data], { type: 'application/zip' }))
      const link = document.createElement('a')
      link.href = url
      link.download = `${values.mode}-bulk.zip`
      link.click()
    } catch (err) {
      setError('Bulk generation failed.')
    } finally {
      setLoading(false)
    }
  }

  const previewRows = () => {
    if (!bulkFile) return
    Papa.parse(bulkFile, {
      header: true,
      skipEmptyLines: true,
      complete: results => setRows(results.data)
    })
  }

  return (
    <div className="app-shell">
      <div className="panel">
        <h1>QR & Barcode Creator</h1>

        <div className="control-row">
          <label>Mode</label>
          <select value={values.mode} onChange={e => setValue('mode', e.target.value)}>
            <option value="qrcode">QR Code</option>
            <option value="barcode">Barcode</option>
          </select>
        </div>

        <div className="control-row">
          <label>Text</label>
          <input value={values.text} onChange={e => setValue('text', e.target.value)} placeholder="Enter code text" />
        </div>
        <div className="control-row">
          <label>Heading</label>
          <input value={values.heading} onChange={e => setValue('heading', e.target.value)} placeholder="1-25 chars" maxLength={25} />
        </div>
        <div className="control-row">
          <label>Description</label>
          <textarea value={values.description} onChange={e => setValue('description', e.target.value)} placeholder="0-75 chars" maxLength={75} rows={3} />
        </div>

        <div className="control-row">
          <label>Foreground</label>
          <SketchPicker color={values.foreground} onChange={color => setValue('foreground', color.hex)} />
        </div>
        <div className="control-row">
          <label>Background</label>
          <SketchPicker color={values.background} onChange={color => setValue('background', color.hex)} />
        </div>

        <div className="control-row-inline">
          <label>Font size</label>
          <input type="number" min={10} max={72} value={values.fontSize} onChange={e => setValue('fontSize', Number(e.target.value))} />
          <label>Font family</label>
          <select value={values.fontFamily} onChange={e => setValue('fontFamily', e.target.value)}>
            <option>Arial</option>
            <option>Helvetica</option>
            <option>Times New Roman</option>
            <option>Courier New</option>
            <option>Georgia</option>
          </select>
        </div>

        <div className="control-row-inline">
          <label>
            <input type="checkbox" checked={values.useGradient} onChange={e => setValue('useGradient', e.target.checked)} />
            Use gradient background
          </label>
        </div>
        {values.useGradient && (
          <div className="control-row-inline">
            <label>From</label>
            <input type="color" value={values.gradientFrom} onChange={e => setValue('gradientFrom', e.target.value)} />
            <label>To</label>
            <input type="color" value={values.gradientTo} onChange={e => setValue('gradientTo', e.target.value)} />
          </div>
        )}

        {values.mode === 'qrcode' && (
          <div className="control-row">
            <label>Center logo/image</label>
            <input type="file" accept="image/*" onChange={e => handleFileChange('logo', e.target.files?.[0] ?? null)} />
          </div>
        )}
        <div className="control-row">
          <label>Background image</label>
          <input type="file" accept="image/*" onChange={e => handleFileChange('bgImage', e.target.files?.[0] ?? null)} />
        </div>

        {values.mode === 'barcode' && (
          <div className="control-row">
            <label>Barcode type</label>
            <select value={values.barcodeType} onChange={e => setValue('barcodeType', e.target.value)}>
              <option value="code128">Code 128</option>
              <option value="ean13">EAN-13</option>
              <option value="ean8">EAN-8</option>
              <option value="upca">UPC-A</option>
            </select>
          </div>
        )}

        <div className="button-row">
          <button onClick={handleGenerate} disabled={loading}>Generate</button>
          <button onClick={handleDownloadPreview} disabled={!previewUrl}>Download Image</button>
        </div>

        {error && <div className="error-box">{error}</div>}
        {previewUrl && <img className="preview-image" src={previewUrl} alt="Preview" />}

        <hr />
        <h2>Bulk CSV Generation</h2>
        <div className="control-row">
          <label>CSV File</label>
          <input type="file" accept=".csv,text/csv" ref={fileInputRef} onChange={e => setBulkFile(e.target.files?.[0] ?? null)} />
        </div>
        <div className="button-row">
          <button onClick={previewRows} disabled={!bulkFile}>Preview CSV</button>
          <button onClick={handleBulkUpload} disabled={!bulkFile || loading}>Download Bulk ZIP</button>
        </div>
        {rows.length > 0 && (
          <div className="csv-preview">
            <strong>CSV preview:</strong>
            <ul>
              {rows.slice(0, 5).map((row, idx) => (
                <li key={idx}>{row.text || '[missing text]'} — {row.heading} — {row.description}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
