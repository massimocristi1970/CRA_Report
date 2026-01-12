# TransUnion CRA Report Analyzer 📊

A web-based Streamlit application for analyzing TransUnion Credit Reference Agency (CRA) report data. This tool handles large files (200MB+) and provides flexible searching and filtering capabilities across all data columns.

## Features ✨

- **🔍 Smart Status Code Extraction**: Automatically extracts status codes (A, M, P, V) from Column 7
- **⚡ Quick Filters**: One-click filtering buttons for each status code
- **🔎 Account ID Search**: Fast lookup with exact or partial matching
- **👤 Name & Address Search**: Filter by first name, last name, and postcode
- **🔧 Advanced Column Search**: Search and filter any column
- **📥 CSV Export**: Download filtered results instantly
- **📊 Large File Support**: Efficiently processes files up to 200MB
- **📄 Smart Pagination**: Browse large datasets with customizable page sizes
- **🎯 Auto-Detection**: Intelligent column structure detection

## Data Format

The application expects tab or space-delimited text files with the following structure:

```
864652  2.24062E+32  0  0  0  0  AMiss  Sarah  Lawrence  70  VICTORIA  AVENUE  SOUTHEND-ON-SEA  SS2  6EB  19051979  0  0000000M
590885  2.27072E+32  0  0  0  0  MMiss  Charlotte  Giles  Grecian  Street  Maidstone  Kent  ME14  2TS000000024051996  0  0000000M
```

### Column Structure

- **Column 1**: Account ID
- **Column 7**: Status Code + Title (e.g., "AMiss", "VMr", "PMiss", "MMiss")
  - First character = Status Code (**A**, **M**, **P**, **V**)
  - Remaining characters = Title
- **Columns 8-9**: First Name, Last Name
- **Remaining columns**: Address fields, dates, numeric codes

## Installation 🚀

### Local Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/massimocristi1970/CRA_Report.git
   cd CRA_Report
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```

5. **Access the app**: Open your browser to `http://localhost:8501`

## Usage Guide 📖

### 1. Upload Your Data

- Click the **"Choose a CRA report file"** button in the sidebar
- Select your tab or space-delimited `.txt` file
- The app will automatically parse and load the data

### 2. Filter Your Data

**Quick Status Code Filters:**
- Click **A**, **M**, **P**, or **V** buttons for instant filtering
- Or use the multi-select dropdown to combine multiple status codes

**Account ID Search:**
- Enter an account ID in the search field
- Toggle "Exact match" for precise lookups
- Leave unchecked for partial matching

**Name & Address Search:**
- Filter by first name, last name, or both
- Search postcodes across both postcode fields

**Advanced Search:**
- Select any column from the dropdown
- Enter a search value to filter that column

### 3. View and Navigate Results

- See statistics: Total records, filtered records, and percentage shown
- Customize rows per page (50, 100, 250, 500, or 1000)
- Navigate through pages using the page selector
- Sort columns by clicking headers in the data table

### 4. Export Results

- Click **"Download Filtered Results (CSV)"** to export
- File includes only the filtered data
- Filename includes timestamp for easy tracking

### 5. Reset Filters

- Click **"Reset All Filters"** to start fresh
- All filters will be cleared instantly

## Deployment to Streamlit Cloud 🌐

Deploy this app for free on Streamlit Cloud:

### Prerequisites

- GitHub account
- Streamlit Cloud account (sign up at [streamlit.io/cloud](https://streamlit.io/cloud))

### Deployment Steps

1. **Fork or push this repository** to your GitHub account

2. **Log in to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

3. **Create a new app**:
   - Click "New app"
   - Select your repository: `massimocristi1970/CRA_Report`
   - Branch: `main` (or your preferred branch)
   - Main file path: `app.py`
   - Click "Deploy"

4. **Wait for deployment**:
   - Streamlit Cloud will install dependencies
   - Your app will be live in a few minutes

5. **Access your app**:
   - URL will be: `https://[your-app-name].streamlit.app`
   - Share this URL with your team

### Team Access Setup

**Option 1: Public Access** (No authentication)
- Your deployed app is public by default
- Share the URL with team members
- No login required

**Option 2: Restricted Access** (Streamlit Cloud Pro)
- Upgrade to Streamlit Cloud Pro for password protection
- Configure allowed email domains
- Set up SSO integration

### Configuration

The `.streamlit/config.toml` file is already configured for optimal performance:
- Max upload size: 500MB
- Optimized theme
- Security settings enabled

## Technical Details 🔧

### Performance Optimizations

- **Chunked Processing**: Large files are processed efficiently
- **Caching**: File parsing is cached with `@st.cache_data`
- **Pagination**: Only displays requested rows at a time
- **Lazy Loading**: Data is loaded progressively

### Error Handling

- Validates file format on upload
- Handles malformed rows gracefully
- Displays helpful error messages
- Provides sample data format on errors

### Status Code Extraction Logic

```python
# Extract first character as Status Code
df['Status_Code'] = df['Status_Title'].str[0]

# Extract remaining characters as Title
df['Title'] = df['Status_Title'].str[1:]
```

## File Structure 📁

```
CRA_Report/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
└── .streamlit/
    └── config.toml            # Streamlit configuration
```

## Requirements 📦

- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0

## Troubleshooting 🔧

### File Upload Issues

**Problem**: "Failed to parse the file"
- **Solution**: Ensure your file is tab or space-delimited
- Check that rows have consistent structure
- Verify Column 7 contains status codes

**Problem**: File upload fails or times out
- **Solution**: Check file size (should be under 500MB)
- Try using a faster internet connection
- For local deployment, increase timeout in config.toml

### Performance Issues

**Problem**: App is slow with large files
- **Solution**: 
  - Use pagination with smaller page sizes
  - Apply filters to reduce displayed data
  - Clear browser cache
  - Restart the Streamlit app

### Filtering Issues

**Problem**: Filters not working as expected
- **Solution**:
  - Click "Reset All Filters" and try again
  - Check for extra spaces in search fields
  - Verify column names match expected format

## Contributing 🤝

Contributions are welcome! Please feel free to submit issues or pull requests.

## License 📄

This project is licensed under the MIT License.

## Support 💬

For questions or issues:
- Open an issue on GitHub
- Contact the repository owner

## Changelog 📝

### Version 1.0.0
- Initial release
- File upload and parsing
- Status code extraction
- Multi-column filtering
- CSV export functionality
- Pagination support
- Streamlit Cloud ready