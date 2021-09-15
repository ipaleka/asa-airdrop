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
SENDER_ADDRESS = "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE"
SENDER_PASSPHRASE = ""  # 25 words separated by spaces
VALID_BLOCK_RANGE_FOR_AIRDROP = ()  # (start, end); leave empty for all opt-ins

SLEEP_INTERVAL = 1  # AlgoExplorer limit for public calls
AIRDROP_AMOUNT = 3000
TRANSACTION_NOTE = "Airdrop"
```

Save the file afterwards and run it with:

```bash
(airdrop) $ python airdrop.py
```
