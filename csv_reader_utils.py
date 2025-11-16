"""
Robust CSV Reader Utility
Handles encoding and delimiter detection issues for CSV files
"""

import pandas as pd
import chardet
from typing import Optional, Tuple, Any
import io


def detect_csv_properties(file_content: bytes) -> Tuple[str, str]:
    """Detect encoding and delimiter for CSV file
    
    Args:
        file_content: Raw bytes content of the CSV file
        
    Returns:
        Tuple of (encoding, delimiter)
    """
    # Detect encoding
    encoding_result = chardet.detect(file_content)
    encoding = encoding_result.get('encoding', 'utf-8')
    
    # Common encodings to try if chardet fails
    encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for enc in encodings_to_try:
        try:
            # Try to decode a sample
            sample_text = file_content[:2048].decode(enc, errors='ignore')
            
            # Count potential delimiters in the first few lines
            lines = sample_text.split('\n')[:5]  # Check first 5 lines
            if not lines:
                continue
                
            delimiter_counts = {}
            for delimiter in [',', ';', '\t', '|']:
                count = sum(line.count(delimiter) for line in lines)
                delimiter_counts[delimiter] = count
            
            # Find the most common delimiter
            best_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])
            
            # If we found a reasonable delimiter (appears in multiple lines)
            if best_delimiter[1] > 0:
                return enc, best_delimiter[0]
                
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    # Default fallback
    return 'utf-8', ','


def robust_read_csv(uploaded_file: Any, **kwargs) -> Optional[pd.DataFrame]:
    """Robustly read CSV file with automatic encoding and delimiter detection
    
    Args:
        uploaded_file: Streamlit uploaded file object or file path
        **kwargs: Additional arguments to pass to pd.read_csv
        
    Returns:
        DataFrame if successful, None if failed
    """
    # Reset file pointer if it's a file object
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    
    # Read file content
    if hasattr(uploaded_file, 'read'):
        file_content = uploaded_file.read()
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
    else:
        # If it's a file path
        with open(uploaded_file, 'rb') as f:
            file_content = f.read()
    
    # Detect properties
    encoding, delimiter = detect_csv_properties(file_content)
    
    # List of parameter combinations to try
    read_attempts = [
        # Try with detected encoding and delimiter
        {'encoding': encoding, 'sep': delimiter},
        # Try with detected encoding and auto-delimiter
        {'encoding': encoding, 'sep': None},
        # Try common encodings with detected delimiter
        {'encoding': 'utf-8', 'sep': delimiter},
        {'encoding': 'latin-1', 'sep': delimiter},
        {'encoding': 'cp1252', 'sep': delimiter},
        # Try common encodings with auto-delimiter
        {'encoding': 'utf-8', 'sep': None},
        {'encoding': 'latin-1', 'sep': None},
        {'encoding': 'cp1252', 'sep': None},
        # Try with Python's csv sniffer
        {'encoding': encoding, 'sep': None, 'engine': 'python'},
        # Last resort - try with explicit common delimiters
        {'encoding': encoding, 'sep': ','},
        {'encoding': encoding, 'sep': ';'},
        {'encoding': encoding, 'sep': '\t'},
    ]
    
    # Try reading with different parameters
    for attempt_params in read_attempts:
        try:
            # Merge with user-provided kwargs
            params = {**attempt_params, **kwargs}
            
            # Reset file pointer
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
            
            # Try to read
            df = pd.read_csv(uploaded_file, **params)
            
            # Validate the result
            if df is not None and not df.empty and len(df.columns) > 0:
                # Additional validation - check if we actually have meaningful data
                if not df.columns.astype(str).str.contains('Unnamed:').all():
                    print(f"Successfully read CSV with encoding='{params.get('encoding')}', sep='{params.get('sep')}'")
                    return df
            
        except Exception as e:
            # Continue to next attempt
            continue
    
    # If all attempts failed, try one more time with very permissive settings
    try:
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        
        # Last resort - read as text and try to parse manually
        text_content = file_content.decode('utf-8', errors='replace')
        
        # Try to create a StringIO object
        string_buffer = io.StringIO(text_content)
        df = pd.read_csv(string_buffer, sep=None, engine='python', encoding=None)
        
        if df is not None and not df.empty and len(df.columns) > 0:
            print("Successfully read CSV with fallback method")
            return df
            
    except Exception as e:
        print(f"All CSV reading attempts failed. Last error: {e}")
        return None
    
    return None


def get_csv_info(uploaded_file: Any) -> dict:
    """Get information about a CSV file without fully loading it
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Dictionary with file information
    """
    try:
        # Reset file pointer
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        
        # Read a sample
        if hasattr(uploaded_file, 'read'):
            sample_content = uploaded_file.read(2048)
            if hasattr(uploaded_file, 'seek'):
                uploaded_file.seek(0)
        else:
            with open(uploaded_file, 'rb') as f:
                sample_content = f.read(2048)
        
        # Detect encoding and delimiter
        encoding, delimiter = detect_csv_properties(sample_content)
        
        # Try to read first few rows to get column info
        df_sample = robust_read_csv(uploaded_file, nrows=5)
        
        if df_sample is not None:
            return {
                'encoding': encoding,
                'delimiter': delimiter,
                'columns': len(df_sample.columns),
                'sample_columns': list(df_sample.columns),
                'readable': True
            }
        else:
            return {
                'encoding': encoding,
                'delimiter': delimiter,
                'columns': 0,
                'sample_columns': [],
                'readable': False,
                'error': 'Could not read file'
            }
            
    except Exception as e:
        return {
            'encoding': 'unknown',
            'delimiter': 'unknown',
            'columns': 0,
            'sample_columns': [],
            'readable': False,
            'error': str(e)
        }