# QR and Barcode Creator

A small React + Node.js application for generating single or bulk QR codes and barcodes with custom heading, description, colors, fonts, and optional logos/backgrounds.

## Run locally

1. Install dependencies for both server and client:
   ```bash
   npm run install-all
   ```

2. Start the backend server:
   ```bash
   npm run start:server
   ```

3. Start the frontend UI:
   ```bash
   npm run start:client
   ```

4. Open the app at http://localhost:5173

## API

- `POST /api/generate` — generate a single PNG from form values
- `POST /api/bulk` — upload a CSV and download a ZIP of generated PNGs

CSV columns should include `text`, `heading`, and `description`.
