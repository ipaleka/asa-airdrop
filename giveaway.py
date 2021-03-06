import time
from datetime import datetime

from algosdk import mnemonic
from algosdk.encoding import is_valid_address
from algosdk.error import WrongChecksumError
from algosdk.future.transaction import AssetTransferTxn
from algosdk.v2client import algod, indexer

NETWORK = "testnet"
ASSET_ID = "26713649"
SENDER_ADDRESS = "5VLMDLOFA4BDSNU5QRUBISQCQJYHF5Q2HTXINUS62UNIDXWP5LJ4MHHOUY"
SENDER_PASSPHRASE = ""  # 25 words separated by spaces

SLEEP_INTERVAL = 1  # AlgoExplorer limit for public calls
GIVEAWAY_AMOUNT = 1000
TRANSACTION_NOTE = "Giveaway"
FILENAME = "addresses.txt"


## CLIENTS
def _algod_client():
    """Instantiate and return Algod client object."""
    if NETWORK == "mainnet":
        algod_address = "https://algoexplorerapi.io"
    else:
        algod_address = "https://testnet.algoexplorerapi.io"
    algod_token = ""
    return algod.AlgodClient(
        algod_token, algod_address, headers={"User-Agent": "DoYouLoveMe?"}
    )


def _indexer_client():
    """Instantiate and return Indexer client object."""
    if NETWORK == "mainnet":
        indexer_address = "https://algoexplorerapi.io/idx2"
    else:
        indexer_address = "https://testnet.algoexplorerapi.io/idx2"
    indexer_token = ""
    return indexer.IndexerClient(
        indexer_token, indexer_address, headers={"User-Agent": "DoYouLoveMe?"}
    )


## TRANSACTIONS
def _wait_for_confirmation(client, transaction_id, timeout):
    """
    Wait until the transaction is confirmed or rejected, or until 'timeout'
    number of rounds have passed.
    Args:
        transaction_id (str): the transaction to wait for
        timeout (int): maximum number of rounds to wait
    Returns:
        dict: pending transaction information, or throws an error if the transaction
            is not confirmed or rejected in the next timeout rounds
    """
    start_round = client.status()["last-round"] + 1
    current_round = start_round

    while current_round < start_round + timeout:
        try:
            pending_txn = client.pending_transaction_info(transaction_id)
        except Exception:
            return
        if pending_txn.get("confirmed-round", 0) > 0:
            return pending_txn
        elif pending_txn["pool-error"]:
            raise Exception("pool error: {}".format(pending_txn["pool-error"]))
        client.status_after_block(current_round)
        current_round += 1
    raise Exception(
        "pending tx not found in timeout rounds, timeout value = : {}".format(timeout)
    )


def address_generator():
    """Return all addresses for giveaway from a file."""
    with open(FILENAME, "r") as addresses:
        for line in addresses:
            address = line.strip()
            if is_valid_address(address):
                yield address


def check_address(address):
    """Return True if address opted-in for the asset."""
    transactions = _indexer_client().search_transactions_by_address(
        address, asset_id=ASSET_ID
    )
    return True if len(transactions.get("transactions")) > 0 else False


def send_asset(receiver):
    """Send asset to provided receiver address."""

    client = _algod_client()
    params = client.suggested_params()
    note = TRANSACTION_NOTE

    decimals = _algod_client().asset_info(ASSET_ID).get("params").get("decimals")
    amount = GIVEAWAY_AMOUNT * (10 ** decimals)

    unsigned_txn = AssetTransferTxn(
        SENDER_ADDRESS,
        params,
        receiver,
        amount,
        index=ASSET_ID,
        note=note.encode(),
    )
    try:
        signed_txn = unsigned_txn.sign(mnemonic.to_private_key(SENDER_PASSPHRASE))
    except WrongChecksumError:
        return "Checksum failed to validate"
    except ValueError:
        return "Unknown word in passphrase"

    try:
        transaction_id = client.send_transaction(signed_txn)
        _wait_for_confirmation(client, transaction_id, 4)
    except Exception as err:
        return str(err)

    print(f"Amount of {GIVEAWAY_AMOUNT} sent to {receiver}")
    return ""


if __name__ == "__main__":

    formatted_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    error_filename = "error_{}.txt".format(formatted_time)
    not_opted_in_filename = "not_opted_in_{}.txt".format(formatted_time)

    for address in address_generator():
        time.sleep(SLEEP_INTERVAL)
        if check_address(address):
            time.sleep(SLEEP_INTERVAL)
            response = send_asset(address)
            if response != "":
                with open(error_filename, "a") as error:
                    error.write(f"{response}\n")
        else:
            with open(not_opted_in_filename, "a") as not_opted_in:
                not_opted_in.write(f"{address}\n")
