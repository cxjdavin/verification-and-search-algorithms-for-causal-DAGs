# Clone dct-policy repository
git clone https://github.com/csquires/dct-policy.git
cd dct-policy

# Setup dct-policy environment
# Note: Given setup script has some missing pip installs
bash setup.sh
source venv/bin/activate
pip install seaborn tqdm ipdb p_tqdm
pip install networkx --upgrade

# Grab PADS source files
wget -r --no-parent --no-host-directories --cut-dirs=1 http://www.ics.uci.edu/\~eppstein/PADS/

# Copy our files into dct-policy folder
cp ../our_code/*.py .
mv pdag.py venv/lib/python3.8/site-packages/causaldag/classes/

# Run experiments to obtain plots
python3 fig1a.py
python3 fig1b.py
python3 fig1c.py
python3 fig1d.py
python3 fig1e.py

# Return to parent directory
cd ..

