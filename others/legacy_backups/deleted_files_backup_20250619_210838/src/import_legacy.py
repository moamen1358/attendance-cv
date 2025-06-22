import sqlite3
import pandas as pd
import os
import logging
import json
import csv
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def import_csv_data(file_path, table_name, column_mapping=None, delimiter=','):
    """
    Import data from CSV file into specified table
    
    Args:
        file_path (str): Path to CSV file
        table_name (str): Name of table to import into
        column_mapping (dict, optional): Mapping of CSV columns to DB columns
        delimiter (str, optional): CSV delimiter character
        
    Returns:
        tuple: (success, message, row_count)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}", 0
        
        # Read CSV file
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Apply column mapping if provided
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            return False, f"Table {table_name} does not exist", 0
        
        # Get columns in the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns = [column[1] for column in cursor.fetchall()]
        
        # Filter dataframe to only include columns that exist in the table
        df = df[[col for col in df.columns if col in table_columns]]
        
        # Check if we have any columns left
        if df.empty or len(df.columns) == 0:
            return False, "No matching columns found between CSV and table", 0
        
        # Insert data into table
        row_count = 0
        for _, row in df.iterrows():
            # Extract non-null values
            columns = []
            values = []
            
            for col in df.columns:
                if pd.notna(row[col]):
                    columns.append(col)
                    values.append(row[col])
            
            if not columns:
                continue
            
            # Build dynamic INSERT query
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join(columns)
            
            query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            if cursor.rowcount > 0:
                row_count += 1
        
        conn.commit()
        return True, f"Successfully imported {row_count} rows into {table_name}", row_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing CSV data: {e}")
        return False, f"Error: {str(e)}", 0
    
    finally:
        conn.close()

def import_json_data(file_path, table_name, key_field=None):
    """
    Import data from JSON file into specified table
    
    Args:
        file_path (str): Path to JSON file
        table_name (str): Name of table to import into
        key_field (str, optional): Field to use as key for upsert operations
        
    Returns:
        tuple: (success, message, row_count)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}", 0
        
        # Read JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle both array and object formats
        if isinstance(data, dict):
            # Convert object to array of objects
            if key_field:
                data = [{key_field: k, **v} if isinstance(v, dict) else {key_field: k, "value": v} 
                        for k, v in data.items()]
            else:
                data = [{"key": k, "value": v} for k, v in data.items()]
        
        if not isinstance(data, list):
            return False, "JSON data must be an array of objects or a dictionary", 0
        
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            return False, f"Table {table_name} does not exist", 0
        
        # Get columns in the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_columns = [column[1] for column in cursor.fetchall()]
        
        # Insert data into table
        row_count = 0
        for item in data:
            if not isinstance(item, dict):
                continue
                
            # Extract values that match table columns
            columns = []
            values = []
            
            for col in table_columns:
                if col in item and item[col] is not None:
                    columns.append(col)
                    values.append(item[col])
            
            if not columns:
                continue
            
            # Build dynamic INSERT query
            placeholders = ', '.join(['?'] * len(columns))
            columns_str = ', '.join(columns)
            
            query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            if cursor.rowcount > 0:
                row_count += 1
        
        conn.commit()
        return True, f"Successfully imported {row_count} rows into {table_name}", row_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error importing JSON data: {e}")
        return False, f"Error: {str(e)}", 0
    
    finally:
        conn.close()

def detect_csv_format(file_path):
    """
    Detect CSV format and suggest column mapping
    
    Args:
        file_path (str): Path to CSV file
        
    Returns:
        tuple: (delimiter, columns, mapping_suggestion)
    """
    try:
        # Try to detect delimiter
        with open(file_path, 'r', newline='') as f:
            sample = f.read(4096)
            
        # Count possible delimiters
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample.count(d) for d in delimiters}
        delimiter = max(counts.items(), key=lambda x: x[1])[0]
        
        # Read first few rows
        df = pd.read_csv(file_path, delimiter=delimiter, nrows=5)
        
        # Standardize column names
        columns = df.columns.tolist()
        
        # Create mapping suggestion
        mapping_suggestion = {}
        for col in columns:
            # Convert to lowercase and remove special characters
            normalized = col.lower().strip().replace(' ', '_')
            
            # Common mappings
            if 'name' in normalized:
                mapping_suggestion[col] = 'name' if 'student_name' not in mapping_suggestion.values() else 'student_name'
            elif 'date' in normalized:
                mapping_suggestion[col] = 'date'
            elif 'time' in normalized:
                mapping_suggestion[col] = 'time'
            elif 'id' in normalized:
                mapping_suggestion[col] = 'id'
            elif 'subject' in normalized:
                mapping_suggestion[col] = 'subject'
            else:
                mapping_suggestion[col] = normalized[:20]  # Limit length
        
        return delimiter, columns, mapping_suggestion
        
    except Exception as e:
        logger.error(f"Error detecting CSV format: {e}")
        return ',', [], {}

def export_table_to_csv(table_name, file_path):
    """
    Export table data to CSV file
    
    Args:
        table_name (str): Name of table to export
        file_path (str): Path to save CSV file
        
    Returns:
        tuple: (success, message)
    """
    conn = get_db_connection()
    
    try:
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            return False, f"Table {table_name} does not exist"
        
        # Get data
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        # Export to CSV
        df.to_csv(file_path, index=False)
        
        return True, f"Successfully exported {len(df)} rows to {file_path}"
        
    except Exception as e:
        logger.error(f"Error exporting table: {e}")
        return False, f"Error: {str(e)}"
    
    finally:
        conn.close()
