cat << 'EOF' > ~/run_tars.sh
#!/bin/bash
cd PUT/PROJECT'S/DIRECTORY/HERE
source venv/bin/activate
python tars.py

echo ""
read -p "Press [Enter] to close..."
EOF

chmod +x ~/run_tars.sh
