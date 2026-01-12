"""
TransUnion CRA Report Analyzer
A Streamlit application for analyzing Credit Reference Agency report data.
"""

import streamlit as st
import pandas as pd
import io
import re
from typing import Tuple, Optional

# Page configuration
st.set_page_config(
    page_title="TransUnion CRA Report Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DEFAULT_COLUMN_NAMES = [
    "Account_ID",
    "Column_2",
    "Column_3",
    "Column_4",
    "Column_5",
    "Column_6",
    "Status_Title",
    "First_Name",
    "Last_Name",
    "Address_Line_1",
    "Address_Line_2",
    "City",
    "County",
    "Postcode_1",
    "Postcode_2",
    "Date_Field",
    "Column_17",
    "Column_18"
]

STATUS_CODES = ['A', 'M', 'P', 'V']

# Helper Functions

@st.cache_data
def parse_data_file(_uploaded_file) -> Tuple[pd.DataFrame, bool]:
    """
    Parse the uploaded data file with intelligent delimiter detection.
    
    Args:
        _uploaded_file: Streamlit UploadedFile object (prefixed with _ to avoid hashing)
        
    Returns:
        Tuple of (DataFrame, success_flag)
    """
    try:
        # Read file content
        content = _uploaded_file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        # Split into lines
        lines = text_content.strip().split('\n')
        
        if not lines:
            return pd.DataFrame(), False
        
        # Parse each line - handle tab or multiple spaces as delimiters
        data_rows = []
        max_columns = 0
        
        for line in lines:
            # Replace tabs with spaces first, then split on multiple spaces
            line = line.replace('\t', ' ')
            # Split on one or more spaces
            parts = [p.strip() for p in re.split(r'\s+', line.strip()) if p.strip()]
            data_rows.append(parts)
            max_columns = max(max_columns, len(parts))
        
        # Pad rows to have equal columns
        for row in data_rows:
            while len(row) < max_columns:
                row.append('')
        
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Assign column names
        if len(df.columns) <= len(DEFAULT_COLUMN_NAMES):
            df.columns = DEFAULT_COLUMN_NAMES[:len(df.columns)]
        else:
            # Generate more column names if needed
            column_names = DEFAULT_COLUMN_NAMES.copy()
            for i in range(len(DEFAULT_COLUMN_NAMES), len(df.columns)):
                column_names.append(f"Column_{i+1}")
            df.columns = column_names
        
        return df, True
        
    except Exception as e:
        st.error(f"Error parsing file: {str(e)}")
        return pd.DataFrame(), False


def extract_status_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract status code from the Status_Title column (column 7).
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with Status_Code and Title columns added
    """
    if 'Status_Title' not in df.columns:
        return df
    
    # Extract first character as Status Code
    df['Status_Code'] = df['Status_Title'].astype(str).str[0]
    
    # Extract remaining characters as Title
    df['Title'] = df['Status_Title'].astype(str).str[1:]
    
    # Reorder columns to put Status_Code and Title after Status_Title
    cols = df.columns.tolist()
    status_title_idx = cols.index('Status_Title')
    
    # Remove Status_Code and Title from their current positions
    cols.remove('Status_Code')
    cols.remove('Title')
    
    # Insert them right after Status_Title
    cols.insert(status_title_idx + 1, 'Status_Code')
    cols.insert(status_title_idx + 2, 'Title')
    
    df = df[cols]
    
    return df


def filter_dataframe(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply filters to the DataFrame.
    
    Args:
        df: Input DataFrame
        filters: Dictionary of filter criteria
        
    Returns:
        Filtered DataFrame
    """
    filtered_df = df.copy()
    
    # Account ID filter
    if filters.get('account_id'):
        account_search = str(filters['account_id']).strip()
        if filters.get('exact_match'):
            filtered_df = filtered_df[filtered_df['Account_ID'] == account_search]
        else:
            filtered_df = filtered_df[filtered_df['Account_ID'].astype(str).str.contains(account_search, case=False, na=False)]
    
    # Status code filter
    if filters.get('status_codes'):
        filtered_df = filtered_df[filtered_df['Status_Code'].isin(filters['status_codes'])]
    
    # Text search filters for other columns
    if filters.get('first_name'):
        filtered_df = filtered_df[filtered_df['First_Name'].astype(str).str.contains(filters['first_name'], case=False, na=False)]
    
    if filters.get('last_name'):
        filtered_df = filtered_df[filtered_df['Last_Name'].astype(str).str.contains(filters['last_name'], case=False, na=False)]
    
    if filters.get('postcode'):
        # Search in both postcode columns
        postcode_mask = (
            filtered_df['Postcode_1'].astype(str).str.contains(filters['postcode'], case=False, na=False) |
            filtered_df['Postcode_2'].astype(str).str.contains(filters['postcode'], case=False, na=False)
        )
        filtered_df = filtered_df[postcode_mask]
    
    # Generic column search
    if filters.get('search_column') and filters.get('search_value'):
        col = filters['search_column']
        val = filters['search_value']
        if col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]
    
    return filtered_df


def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode('utf-8')


# Main Application

def main():
    """Main application function."""
    
    # Title and description
    st.title("📊 TransUnion CRA Report Analyzer")
    st.markdown("""
    Upload your TransUnion CRA report file to analyze and filter the data.
    Supports large files (up to 500MB) with tab or space-delimited format.
    """)
    
    # File upload
    st.sidebar.header("📁 File Upload")
    uploaded_file = st.sidebar.file_uploader(
        "Choose a CRA report file",
        type=['txt'],
        help="Upload a tab or space-delimited text file (max 500MB)"
    )
    
    if uploaded_file is not None:
        # Show file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.sidebar.success(f"File uploaded: {uploaded_file.name}")
        st.sidebar.info(f"Size: {file_size_mb:.2f} MB")
        
        # Parse the file
        with st.spinner("Loading and parsing file..."):
            df, success = parse_data_file(uploaded_file)
        
        if not success or df.empty:
            st.error("Failed to parse the file. Please check the file format.")
            st.info("""
            **Expected format:**
            - Tab or space-delimited text file
            - Each row should contain account information
            - Column 7 should contain status code + title (e.g., 'AMiss', 'VMr')
            """)
            return
        
        # Extract status codes
        df = extract_status_code(df)
        
        # Display total record count
        st.success(f"✅ Successfully loaded {len(df):,} records")
        
        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        
        # Initialize filters dictionary
        filters = {}
        
        # Status Code Filter (Quick buttons)
        st.sidebar.subheader("Status Code")
        col1, col2, col3, col4 = st.sidebar.columns(4)
        
        selected_status_codes = []
        with col1:
            if st.button("A", use_container_width=True, help="Filter by Status Code A"):
                selected_status_codes = ['A']
        with col2:
            if st.button("M", use_container_width=True, help="Filter by Status Code M"):
                selected_status_codes = ['M']
        with col3:
            if st.button("P", use_container_width=True, help="Filter by Status Code P"):
                selected_status_codes = ['P']
        with col4:
            if st.button("V", use_container_width=True, help="Filter by Status Code V"):
                selected_status_codes = ['V']
        
        # Multi-select for status codes
        status_multiselect = st.sidebar.multiselect(
            "Or select multiple:",
            options=STATUS_CODES,
            default=selected_status_codes if selected_status_codes else None,
            help="Select one or more status codes to filter"
        )
        
        if status_multiselect:
            filters['status_codes'] = status_multiselect
        
        st.sidebar.divider()
        
        # Account ID Filter
        st.sidebar.subheader("Account ID")
        account_id = st.sidebar.text_input(
            "Search Account ID",
            help="Search by account ID (Column 1)"
        )
        exact_match = st.sidebar.checkbox("Exact match", value=False)
        
        if account_id:
            filters['account_id'] = account_id
            filters['exact_match'] = exact_match
        
        st.sidebar.divider()
        
        # Name filters
        st.sidebar.subheader("Name Search")
        first_name = st.sidebar.text_input("First Name")
        last_name = st.sidebar.text_input("Last Name")
        
        if first_name:
            filters['first_name'] = first_name
        if last_name:
            filters['last_name'] = last_name
        
        st.sidebar.divider()
        
        # Postcode filter
        st.sidebar.subheader("Address")
        postcode = st.sidebar.text_input("Postcode", help="Search in postcode fields")
        
        if postcode:
            filters['postcode'] = postcode
        
        st.sidebar.divider()
        
        # Advanced search - any column
        st.sidebar.subheader("Advanced Search")
        search_column = st.sidebar.selectbox(
            "Select Column",
            options=[''] + list(df.columns),
            help="Search in any column"
        )
        search_value = st.sidebar.text_input("Search Value")
        
        if search_column and search_value:
            filters['search_column'] = search_column
            filters['search_value'] = search_value
        
        # Reset filters button
        if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
            filters = {}
            st.rerun()
        
        # Apply filters
        filtered_df = filter_dataframe(df, filters)
        
        # Display results
        st.header("📋 Results")
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", f"{len(df):,}")
        with col2:
            st.metric("Filtered Records", f"{len(filtered_df):,}")
        with col3:
            if len(df) > 0:
                filter_pct = (len(filtered_df) / len(df)) * 100
                st.metric("Showing", f"{filter_pct:.1f}%")
        
        # Export button
        if len(filtered_df) > 0:
            csv_data = convert_df_to_csv(filtered_df)
            st.download_button(
                label="📥 Download Filtered Results (CSV)",
                data=csv_data,
                file_name=f"cra_report_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.divider()
        
        # Pagination settings
        st.subheader("Data Preview")
        rows_per_page = st.selectbox(
            "Rows per page:",
            options=[50, 100, 250, 500, 1000],
            index=1
        )
        
        # Calculate pagination
        total_rows = len(filtered_df)
        total_pages = (total_rows - 1) // rows_per_page + 1 if total_rows > 0 else 0
        
        if total_pages > 0:
            page = st.number_input(
                f"Page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )
            
            # Calculate slice
            start_idx = (page - 1) * rows_per_page
            end_idx = min(start_idx + rows_per_page, total_rows)
            
            # Display paginated data
            st.dataframe(
                filtered_df.iloc[start_idx:end_idx],
                use_container_width=True,
                height=600
            )
            
            st.caption(f"Showing rows {start_idx + 1} to {end_idx} of {total_rows:,}")
        else:
            st.info("No records match the current filters.")
    
    else:
        # Show instructions when no file is uploaded
        st.info("👈 Please upload a CRA report file to begin analysis")
        
        st.subheader("📖 Expected File Format")
        st.markdown("""
        The application expects a tab or space-delimited text file with the following structure:
        
        - **Column 1**: Account ID
        - **Column 7**: Status Code + Title (e.g., 'AMiss', 'VMr', 'PMiss', 'MMiss')
            - First character is the status code: **A**, **M**, **P**, or **V**
        - **Columns 8-9**: First Name, Last Name
        - **Remaining columns**: Address fields, dates, and numeric codes
        
        **Sample data:**
        ```
        864652  2.24062E+32  0  0  0  0  AMiss  Sarah  Lawrence  70  VICTORIA  AVENUE  ...
        590885  2.27072E+32  0  0  0  0  MMiss  Charlotte  Giles  Grecian  Street  ...
        ```
        """)
        
        st.subheader("✨ Features")
        st.markdown("""
        - 🔍 **Quick Status Code Filters**: One-click filtering by A, M, P, or V
        - 🔎 **Account ID Search**: Fast lookup with exact or partial matching
        - 👤 **Name Search**: Filter by first name, last name, or both
        - 📮 **Postcode Search**: Search across postcode fields
        - 🔧 **Advanced Search**: Filter any column with text search
        - 📥 **Export Results**: Download filtered data as CSV
        - 📊 **Large File Support**: Efficiently handles files up to 500MB
        - 📄 **Pagination**: Browse large datasets with ease
        """)


if __name__ == "__main__":
    main()
