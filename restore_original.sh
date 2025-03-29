#!/bin/bash

# Go to your project directory
cd /home/invisa/Desktop/my_grad_streamlit

# Rename main.py back to app.py if needed
if [ -f src/main.py ] && [ ! -f src/app.py ]; then
    mv src/main.py src/app.py
    echo "Restored app.py from main.py"
fi

# Restore login.py to use app instead of main
if [ -f src/login.py ]; then
    sed -i 's/import src.main as main_module/import app/g' src/login.py
    echo "Updated login.py imports"
fi

# Make app.py executable
if [ -f src/app.py ]; then
    chmod +x src/app.py
    echo "Made app.py executable"
fi

echo "Basic restoration complete"
