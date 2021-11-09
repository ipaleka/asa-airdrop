import time

from algosdk import mnemonic
from algosdk.constants import MICROALGOS_TO_ALGOS_RATIO
from algosdk.error import WrongChecksumError
from algosdk.future.transaction import AssetTransferTxn
from algosdk.v2client import algod, indexer

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


class NotQualified(Exception):
    """Exception for addresses not passing airdrop conditions."""


class SilentNotQualified(Exception):
    """Silent exception for addresses not passing airdrop conditions."""


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


def check_valid_for_airdrop(item):
    """Raise an exception if provided item doesn't qualify for airdrop."""

    if not ASSET_HOLDERS_INCLUDED and item.get("amount") != 0:
        raise SilentNotQualified

    if MINIMUM_ALGO_HOLDING is not None or MINIMUM_OTHER_ASA_HOLDING > 0:
        account_info = _indexer_client().account_info(item.get("address"))

    if MINIMUM_ALGO_HOLDING is not None:
        if MINIMUM_ALGO_HOLDING < 0.1:
            print(f"Invalid mimimum Algo holding value: {MINIMUM_ALGO_HOLDING}")
            raise SystemExit
        if (
            account_info.get("account").get("amount") / MICROALGOS_TO_ALGOS_RATIO
            < MINIMUM_ALGO_HOLDING
        ):
            raise NotQualified

    if MINIMUM_OTHER_ASA_HOLDING > 0:
        if not isinstance(MINIMUM_OTHER_ASA_HOLDING, int):
            print(
                f"MINIMUM_OTHER_ASA_HOLDING is not an integer: {MINIMUM_OTHER_ASA_HOLDING}"
            )
            raise SystemExit
        assets = [
            asset
            for asset in account_info.get("account").get("assets")
            if asset.get("amount") > 0
        ]
        if len(assets) < MINIMUM_OTHER_ASA_HOLDING:
            raise NotQualified

    if len(VALID_BLOCK_RANGE_FOR_AIRDROP) != 0:
        if len(VALID_BLOCK_RANGE_FOR_AIRDROP) != 2:
            print(f"Invalid block range: {VALID_BLOCK_RANGE_FOR_AIRDROP}")
            raise SystemExit
        if len(VALID_BLOCK_RANGE_FOR_AIRDROP) == 2 and (
            item.get("opted-in-at-round") < VALID_BLOCK_RANGE_FOR_AIRDROP[0]
            or item.get("opted-in-at-round") > VALID_BLOCK_RANGE_FOR_AIRDROP[1]
        ):
            raise NotQualified


def address_generator():
    """Return all addresses opted-in for the asset."""
    balances = _indexer_client().asset_balances(ASSET_ID)
    while balances.get("balances"):
        for item in balances.get("balances"):
            try:
                check_valid_for_airdrop(item)
                yield item
            except NotQualified:
                print(
                    "Address {} is not qualified for airdrop".format(
                        item.get("address")
                    )
                )
            except SilentNotQualified:
                pass
        next_token = balances.get("next-token")
        balances = _indexer_client().asset_balances(ASSET_ID, next_page=next_token)


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

    decimals = _algod_client().asset_info(ASSET_ID).get("params").get("decimals")
    amount = int(AIRDROP_AMOUNT * (10 ** decimals))

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

    print(f"Amount of {AIRDROP_AMOUNT} sent to {receiver}")
    return ""


if __name__ == "__main__":

    for item in address_generator():
        address = item.get("address")
        time.sleep(SLEEP_INTERVAL)
        if ASSET_HOLDERS_INCLUDED or check_address(address):
            time.sleep(SLEEP_INTERVAL)
            response = send_asset(address)
            if response != "":
                print(f"Error: {response}")
                raise SystemExit
