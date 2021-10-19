# Algorand ASA airdrop script

---
**Security warning**

This project has not been audited!

---

# Requirements

You should have Python 3 installed on your system. Also, this tutorial uses `python3-venv` for creating virtual environments - install it in a Debian/Ubuntu based systems by issuing the following command:

```bash
$ sudo apt-get install python3-venv
```


# Setup

Clone the repository:

```bash
git clone https://github.com/ipaleka/asa-airdrop.git
```

As always for the Python-based projects, you should create a Python environment and activate it:

```bash
python3 -m venv airdrop
source airdrop/bin/activate
```

Now change the directory to the project root directory and install the project dependencies with:

```bash
(airdrop) $ pip install -r requirements.txt
```


# Run

At the top of `airdrop.py` file you may find the constants you should change:

```
NETWORK = "testnet"
ASSET_ID = "26713649"
SENDER_ADDRESS = "5VLMDLOFA4BDSNU5QRUBISQCQJYHF5Q2HTXINUS62UNIDXWP5LJ4MHHOUY"
SENDER_PASSPHRASE = ""  # 25 words separated by spaces
VALID_BLOCK_RANGE_FOR_AIRDROP = ()  # (start, end); leave empty for all opt-ins
MINIMUM_ALGO_HOLDING = None  # leave None for global minimum of 0.1
MINIMUM_OTHER_ASA_HOLDING = 0  # leave 0 if account doesn't have to hold other ASA
ASSET_HOLDERS_INCLUDED = False  # set to True if ASA holders are eligible for airdrop

SLEEP_INTERVAL = 1  # AlgoExplorer limit for public calls
AIRDROP_AMOUNT = 3000
TRANSACTION_NOTE = "Airdrop"
```

Save the file afterwards and run it with:

```bash
(airdrop) $ python airdrop.py
```
