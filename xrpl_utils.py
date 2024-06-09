import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import EscrowCreate, EscrowFinish
from xrpl.transaction import autofill_and_sign
from xrpl.transaction import submit
from xrpl.wallet import Wallet

# Connect to the XRPL network (Testnet in this case)
JSON_RPC_URL = "https://s.altnet.rippletest.net:51234/"
client = JsonRpcClient(JSON_RPC_URL)

def create_escrow(wallet: Wallet, destination: str, amount: str):
    escrow_create = EscrowCreate(
        account=wallet.classic_address,
        amount=xrpl.utils.xrp_to_drops(amount),
        destination=destination,
        finish_after=xrpl.utils.ripple_time_now() + 60*60,  # 1 hour from now
    )
    signed_tx = autofill_and_sign(escrow_create, wallet, client)
    response = submit(signed_tx, client)
    return response

def finish_escrow(wallet: Wallet, owner: str, escrow_sequence: int):
    escrow_finish = EscrowFinish(
        account=wallet.classic_address,
        owner=owner,
        offer_sequence=escrow_sequence
    )
    signed_tx = autofill_and_sign(escrow_finish, wallet, client)
    response = submit(signed_tx, client)
    return response
