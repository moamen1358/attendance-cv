#!/bin/bash

echo "Deleting redundant files..."

# Legacy files that have been migrated to the new structure
echo "Removing legacy files..."
rm -f /home/invisa/Desktop/my_grad_streamlit/src/app.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/database_maintenance.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/database_utils.py 
rm -f /home/invisa/Desktop/my_grad_streamlit/src/security.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/error_handler.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/backup_manager.py 
rm -f /home/invisa/Desktop/my_grad_streamlit/src/db_pool.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/run.py

# Files with duplicated functionality
echo "Removing redundant modules..."
rm -f /home/invisa/Desktop/my_grad_streamlit/src/student_report.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/report.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/display_patch.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/initialize_tables.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/bootstrap_tables.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/db_schema_manager.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/database_sync.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/cache_manager.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/schema_repair.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/import_legacy.py

# Cleanup unused utility scripts
echo "Removing utility scripts..."
rm -f /home/invisa/Desktop/my_grad_streamlit/cleanup.sh
rm -f /home/invisa/Desktop/my_grad_streamlit/remove_redundant_files.sh

# Clean cache files
echo "Removing cache files..."
find /home/invisa/Desktop/my_grad_streamlit -name "__pycache__" -type d -exec rm -rf {} +  2>/dev/null || true
find /home/invisa/Desktop/my_grad_streamlit -name "*.pyc" -delete 2>/dev/null || true

echo "File cleanup completed successfully!"
echo "Your project structure is now streamlined and organized."
