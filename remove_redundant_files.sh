#!/bin/bash

echo "Removing redundant files from src directory..."
rm -f /home/invisa/Desktop/my_grad_streamlit/src/initialize_tables.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/run.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/cache_manager.py
rm -f /home/invisa/Desktop/my_grad_streamlit/src/schema_repair.py

echo "Removing redundant scripts..."
rm -f /home/invisa/Desktop/my_grad_streamlit/scripts/fix_*.py
rm -f /home/invisa/Desktop/my_grad_streamlit/scripts/repair_attendance_tables.py
rm -f /home/invisa/Desktop/my_grad_streamlit/scripts/update_subjects_schema.py
rm -f /home/invisa/Desktop/my_grad_streamlit/scripts/rebuild_database.py

echo "Redundant files have been removed."
