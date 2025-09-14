@echo off
echo Fixing numpy/pandas compatibility issue...
pip uninstall pandas numpy -y
pip install --force-reinstall pandas==1.5.3 numpy==1.24.3
pip install -r requirements.txt
echo Dependencies fixed! Starting server...
python app.py
pause
