# Clone dct-policy repository
git clone https://github.com/csquires/dct-policy.git
cd dct-policy

# Setup dct-policy environment
# Note: Given setup script has some missing pip installs
bash setup.sh
source venv/bin/activate
pip install seaborn tqdm ipdb p_tqdm
pip install networkx==2.8.8

# Grab PADS source files
wget -r --no-parent --no-host-directories --cut-dirs=1 http://www.ics.uci.edu/\~eppstein/PADS/

# Copy our files into dct-policy folder
cp ../our_code/*.py .
mv pdag.py venv/lib/python3.8/site-packages/causaldag/classes/

# Run experiments to obtain plots
python3 exp1.py
python3 exp2.py
python3 exp3.py
python3 exp4.py
python3 exp5.py

# Return to parent directory
cd ..

