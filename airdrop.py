import time

from algosdk import mnemonic
from algosdk.error import WrongChecksumError
from algosdk.future.transaction import PaymentTxn
from algosdk.v2client import algod, indexer

ASSET_ID = "26713649"
SENDER_ADDRESS = "LXJ3Q6RZ2TJ6VCJDFMSM4ZVNYYYE4KVSL3N2TYR23PLNCJCIXBM3NYTBYE"
SENDER_PASSPHRASE = "foo"

SLEEP_INTERVAL = 1  # AlgoExplorer limit for public calls
AIRDROP_AMOUNT = 3000
TRANSACTION_NOTE = "Airdrop"


## CLIENTS
def _algod_client():
    """Instantiate and return Algod client object."""
    # algod_address = "https://algoexplorerapi.io/"
    algod_address = "https://testnet.algoexplorerapi.io/"
    algod_token = ""
    return algod.AlgodClient(
        algod_token, algod_address, headers={"User-Agent": "DoYouLoveMe?"}
    )


def _indexer_client():
    """Instantiate and return Indexer client object."""
    # indexer_address = "https://algoexplorerapi.io/idx2"
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
    """Return all addresses opted-in for the asset."""
    balances = _indexer_client().asset_balances(ASSET_ID)
    while balances.get("balances"):
        next_token = balances.get("next-token")
        balances = _indexer_client().asset_balances(ASSET_ID, next_page=next_token)
        for item in balances.get("balances"):
            if item.get("amount") == 0:
                yield item


def check_address(address):
    """Return True if address has only opt-in transaction for the asset."""
    transactions = _indexer_client().search_transactions_by_address(
        address, asset_id=ASSET_ID
    )
    return True if len(transactions.get("transactions")) == 1 else False


def send_asset(receiver):
    """Send asset to provided receiver address."""

    client = _algod_client()
    params = client.suggested_params()
    note = TRANSACTION_NOTE

    unsigned_txn = PaymentTxn(
        SENDER_ADDRESS, params, receiver, AIRDROP_AMOUNT, None, note.encode()
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

    print("Amount of {AIRDROP_AMOUNT} sent to {receiver}")
    return ""


if __name__ == "__main__":

    for item in address_generator():
        address = item.get("address")
        time.sleep(SLEEP_INTERVAL)
        if check_address(address):
            time.sleep(SLEEP_INTERVAL)
            response = send_asset(address)
            if response != "":
                print(f"Error: {response}")
                raise SystemExit
