# TransUnion CRA Report Analyzer

This repository now supports two app modes for working with TransUnion Credit Reference Agency (CRA) report data:

- Streamlit app in `app.py`
- Static web app in `web/` for Cloudflare deployment

The Streamlit version stays available, while the new browser-first version can be hosted on Cloudflare Pages.

## Features

- CRA text parsing with stable trailing-field normalization
- Status code extraction for tagged values such as `AMiss` and `VMr`
- Filters for status code, account ID, name, postcode, and any column
- CSV export of filtered rows
- Single-row export for ad hoc sharing
- Optional cross-file matching against CSV or XLSX extracts

## Local Streamlit Usage

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run app.py
```

## Static Web App

The web app lives in `web/` and runs entirely in the browser. CRA files are parsed client-side, which makes it a good fit for static hosting.

Quick local preview options:

- Open `web/index.html` in a browser
- Or serve the `web/` folder from any static file server

## Deploying To Cloudflare

Cloudflare cannot host the Streamlit runtime directly like Streamlit Cloud, so the Cloudflare target is the static web app.

### Cloudflare Pages

1. Push the repository to GitHub.
2. In Cloudflare Pages, create a new project and connect this repo.
3. Use these settings:
   - Framework preset: `None`
   - Build command: leave blank
   - Build output directory: `web`
4. Deploy.

### Wrangler

A `wrangler.toml` file is included and points static assets to `web/`.

Example:

```bash
wrangler deploy
```

You will need to authenticate Wrangler with your Cloudflare account before deploying.

## Streamlit Cloud

If you still want the hosted Streamlit version, you can deploy `app.py` to Streamlit Cloud exactly as before.

## Tests

Run the existing Python tests with:

```bash
python -m unittest discover -s tests
```

## Project Structure

```text
CRA_Report/
|-- app.py
|-- requirements.txt
|-- web/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
|   `-- _headers
|-- wrangler.toml
`-- tests/
```
