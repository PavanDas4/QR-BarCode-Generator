const express = require('express')
const cors = require('cors')
const multer = require('multer')
const QRCode = require('qrcode')
const bwipjs = require('bwip-js')
const { createCanvas, loadImage } = require('@napi-rs/canvas')
const csv = require('csv-parser')
const archiver = require('archiver')
const { Readable } = require('stream')
const path = require('path')

const app = express()
const upload = multer({ storage: multer.memoryStorage() })
app.use(cors())
app.use(express.json())

const WIDTH = 1200
const HEIGHT = 1200
const PADDING = 64

async function loadImageSafely(fileBuffer) {
  return loadImage(fileBuffer)
}

function drawBackground(ctx, width, height, options) {
  if (options.bgImage) {
    const img = options.bgImage
    const aspect = img.width / img.height
    let drawW = width
    let drawH = height
    if (img.width > img.height) {
      drawH = width / aspect
    } else {
      drawW = height * aspect
    }
    const x = (width - drawW) / 2
    const y = (height - drawH) / 2
    ctx.drawImage(img, x, y, drawW, drawH)
    return
  }

  if (options.useGradient) {
    const gradient = ctx.createLinearGradient(0, 0, width, height)
    gradient.addColorStop(0, options.gradientFrom)
    gradient.addColorStop(1, options.gradientTo)
    ctx.fillStyle = gradient
  } else {
    ctx.fillStyle = options.background
  }
  ctx.fillRect(0, 0, width, height)
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = text.split(' ')
  let line = ''
  let currentY = y

  for (let n = 0; n < words.length; n += 1) {
    const testLine = line + (line ? ' ' : '') + words[n]
    const metrics = ctx.measureText(testLine)
    const testWidth = metrics.width
    if (testWidth > maxWidth && n > 0) {
      ctx.fillText(line, x, currentY)
      line = words[n]
      currentY += lineHeight
    } else {
      line = testLine
    }
  }
  ctx.fillText(line, x, currentY)
  return currentY
}

function drawTextBlock(ctx, width, values) {
  const headingFont = `bold ${values.fontSize + 10}px ${values.fontFamily}`
  const descriptionFont = `300 ${Math.max(12, values.fontSize - 4)}px ${values.fontFamily}`

  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillStyle = values.foreground

  ctx.font = headingFont
  const headingY = PADDING
  ctx.fillText(values.heading, width / 2, headingY)

  ctx.font = descriptionFont
  const descriptionY = headingY + values.fontSize + 28
  const lineHeight = Math.max(20, values.fontSize - 4 + 6)
  wrapText(ctx, values.description, width / 2, descriptionY, width - PADDING * 2, lineHeight)
}

async function generateCodeImage(values) {
  const canvas = createCanvas(WIDTH, HEIGHT)
  const ctx = canvas.getContext('2d')

  await drawBackground(ctx, WIDTH, HEIGHT, values)
  drawTextBlock(ctx, WIDTH, values)

  if (values.mode === 'qrcode') {
    const qrcodeCanvas = createCanvas(860, 860)
    await QRCode.toCanvas(qrcodeCanvas, values.text, {
      margin: 1,
      color: {
        dark: values.foreground,
        light: 'transparent'
      }
    })
    const qrX = (WIDTH - qrcodeCanvas.width) / 2
    const qrY = (HEIGHT - qrcodeCanvas.height) / 2
    ctx.drawImage(qrcodeCanvas, qrX, qrY)

    if (values.logo) {
      const logoSize = 220
      const logoX = (WIDTH - logoSize) / 2
      const logoY = (HEIGHT - logoSize) / 2
      ctx.save()
      ctx.beginPath()
      ctx.arc(logoX + logoSize / 2, logoY + logoSize / 2, logoSize / 2, 0, Math.PI * 2)
      ctx.closePath()
      ctx.clip()
      ctx.drawImage(values.logo, logoX, logoY, logoSize, logoSize)
      ctx.restore()
    }
  } else {
    const barcodeCanvas = createCanvas(1000, 340)
    await bwipjs.toCanvas(barcodeCanvas, {
      bcid: values.barcodeType,
      text: values.text,
      includetext: true,
      textxalign: 'center',
      backgroundcolor: values.background.replace('#', ''),
      paddingwidth: 30,
      paddingheight: 20,
      scale: 3
    })
    const x = (WIDTH - barcodeCanvas.width) / 2
    const y = (HEIGHT - barcodeCanvas.height) / 2
    ctx.drawImage(barcodeCanvas, x, y)
  }

  return canvas
}

async function processCsv(buffer, values) {
  const results = []
  const stream = Readable.from([buffer.toString('utf8')])
  await new Promise((resolve, reject) => {
    stream
      .pipe(csv())
      .on('data', row => {
        const rowValues = {
          ...values,
          text: row.text || row.qrcode_text || row.barcode_text || '',
          heading: row.heading || '',
          description: row.description || ''
        }
        results.push(rowValues)
      })
      .on('end', resolve)
      .on('error', reject)
  })
  return results
}

app.post('/api/generate', upload.fields([{ name: 'logo' }, { name: 'bgImage' }]), async (req, res) => {
  try {
    const body = req.body
    const values = {
      mode: body.mode || 'qrcode',
      text: body.text || '',
      heading: body.heading || '',
      description: body.description || '',
      foreground: body.foreground || '#000000',
      background: body.background || '#ffffff',
      fontSize: Number(body.fontSize) || 20,
      fontFamily: body.fontFamily || 'Arial',
      useGradient: body.useGradient === 'true',
      gradientFrom: body.gradientFrom || '#ffffff',
      gradientTo: body.gradientTo || '#000000',
      barcodeType: body.barcodeType || 'code128'
    }

    if (req.files && req.files.bgImage && req.files.bgImage.length) {
      values.bgImage = await loadImageSafely(req.files.bgImage[0].buffer)
    }
    if (req.files && req.files.logo && req.files.logo.length) {
      values.logo = await loadImageSafely(req.files.logo[0].buffer)
    }

    const canvas = await generateCodeImage(values)
    const buffer = canvas.toBuffer('image/png')
    res.type('image/png').send(buffer)
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Generate failed' })
  }
})

app.post('/api/bulk', upload.fields([{ name: 'csv' }, { name: 'logo' }, { name: 'bgImage' }]), async (req, res) => {
  try {
    if (!req.files || !req.files.csv || !req.files.csv.length) {
      return res.status(400).json({ error: 'CSV file is required' })
    }

    const values = {
      mode: req.body.mode || 'qrcode',
      foreground: req.body.foreground || '#000000',
      background: req.body.background || '#ffffff',
      fontSize: Number(req.body.fontSize) || 20,
      fontFamily: req.body.fontFamily || 'Arial',
      useGradient: req.body.useGradient === 'true',
      gradientFrom: req.body.gradientFrom || '#ffffff',
      gradientTo: req.body.gradientTo || '#000000',
      barcodeType: req.body.barcodeType || 'code128'
    }
    if (req.files.bgImage && req.files.bgImage.length) {
      values.bgImage = await loadImageSafely(req.files.bgImage[0].buffer)
    }
    if (req.files.logo && req.files.logo.length) {
      values.logo = await loadImageSafely(req.files.logo[0].buffer)
    }

    const rows = await processCsv(req.files.csv[0].buffer, values)
    res.attachment(`${values.mode}-bulk.zip`)
    const archive = archiver('zip', { zlib: { level: 9 } })
    archive.pipe(res)

    for (let i = 0; i < rows.length; i += 1) {
      const row = rows[i]
      const canvas = await generateCodeImage(row)
      const buffer = canvas.toBuffer('image/png')
      const fileName = `${values.mode}-${String(i + 1).padStart(3, '0')}.png`
      archive.append(buffer, { name: fileName })
    }

    await archive.finalize()
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Bulk generation failed' })
  }
})

const PORT = process.env.PORT || 4000
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})
