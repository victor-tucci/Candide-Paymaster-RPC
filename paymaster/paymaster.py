import math

from .models import ERC20ApprovedToken
from .serializers import OperationSerialzer

from jsonrpcserver import method, Result, Success, dispatch, Error
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import environ
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from hexbytes import HexBytes
import re
from eth_account.messages import defunct_hash_message

env = environ.Env()


# Todo: check wallet balance if it has the required tokens to pay for the paymaster fees
# Todo: accept the full bundle as an input and check the approve operation
@method
def pm_sponsorUserOperation(request, token_address) -> Result:
    w3 = Web3(Web3.HTTPProvider(env('HTTPProvider')))
    chainId = str(env('chainId'))
    if chainId == "80002":
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    print('\033[96m' + "Paymaster Operation received." + '\033[39m')
    token_object = ERC20ApprovedToken.objects.filter(chains__has_key=chainId).filter(chains__icontains=token_address)
    if len(token_object) < 1:
        return Error(2, "Unsupported token", data="")

    token = token_object.first().chains[chainId]
    if not token["enabled"]:
        return Error(2, "Unsupported token", data="")

    serialzer = OperationSerialzer(data=request)

    if not serialzer.is_valid():
        return Error(400, "BAD REQUEST")

    print('\033[96m' + "Serializs is done." + '\033[39m')
    op = dict(serialzer.data)
    op["maxFeePerGas"] = int(op["maxFeePerGas"], 16)
    op["maxPriorityFeePerGas"] = int(op["maxPriorityFeePerGas"], 16)
    op["callGasLimit"] = int(op["callGasLimit"], 16)
    op["verificationGasLimit"] = int(op["verificationGasLimit"], 16)
    op["preVerificationGas"] = int(op["preVerificationGas"], 16)
    op["nonce"] = int(op["nonce"], 16)

    abi = [
    {
      "inputs": [
        {
          "internalType": "contract IEntryPoint",
          "name": "_entryPoint",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "_owner",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "previousOwner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "OwnershipTransferred",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "sender",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "token",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "cost",
          "type": "uint256"
        }
      ],
      "name": "UserOperationSponsored",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "COST_OF_POST",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint32",
          "name": "unstakeDelaySec",
          "type": "uint32"
        }
      ],
      "name": "addStake",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "contract IERC20Metadata",
          "name": "",
          "type": "address"
        }
      ],
      "name": "balances",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "deposit",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "entryPoint",
      "outputs": [
        {
          "internalType": "contract IEntryPoint",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getDeposit",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "components": [
            {
              "internalType": "address",
              "name": "sender",
              "type": "address"
            },
            {
              "internalType": "uint256",
              "name": "nonce",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "initCode",
              "type": "bytes"
            },
            {
              "internalType": "bytes",
              "name": "callData",
              "type": "bytes"
            },
            {
              "internalType": "uint256",
              "name": "callGasLimit",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "verificationGasLimit",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "preVerificationGas",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "maxFeePerGas",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "maxPriorityFeePerGas",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "paymasterAndData",
              "type": "bytes"
            },
            {
              "internalType": "bytes",
              "name": "signature",
              "type": "bytes"
            }
          ],
          "internalType": "struct UserOperation",
          "name": "userOp",
          "type": "tuple"
        },
        {
          "components": [
            {
              "internalType": "contract IERC20Metadata",
              "name": "token",
              "type": "address"
            },
            {
              "internalType": "enum NoValidationPaymaster.SponsoringMode",
              "name": "mode",
              "type": "uint8"
            },
            {
              "internalType": "uint48",
              "name": "validUntil",
              "type": "uint48"
            },
            {
              "internalType": "uint256",
              "name": "fee",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "exchangeRate",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "signature",
              "type": "bytes"
            }
          ],
          "internalType": "struct NoValidationPaymaster.PaymasterData",
          "name": "paymasterData",
          "type": "tuple"
        }
      ],
      "name": "getHash",
      "outputs": [
        {
          "internalType": "bytes32",
          "name": "",
          "type": "bytes32"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "bytes",
          "name": "paymasterAndData",
          "type": "bytes"
        }
      ],
      "name": "parsePaymasterAndData",
      "outputs": [
        {
          "components": [
            {
              "internalType": "contract IERC20Metadata",
              "name": "token",
              "type": "address"
            },
            {
              "internalType": "enum NoValidationPaymaster.SponsoringMode",
              "name": "mode",
              "type": "uint8"
            },
            {
              "internalType": "uint48",
              "name": "validUntil",
              "type": "uint48"
            },
            {
              "internalType": "uint256",
              "name": "fee",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "exchangeRate",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "signature",
              "type": "bytes"
            }
          ],
          "internalType": "struct NoValidationPaymaster.PaymasterData",
          "name": "",
          "type": "tuple"
        }
      ],
      "stateMutability": "pure",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "enum IPaymaster.PostOpMode",
          "name": "mode",
          "type": "uint8"
        },
        {
          "internalType": "bytes",
          "name": "context",
          "type": "bytes"
        },
        {
          "internalType": "uint256",
          "name": "actualGasCost",
          "type": "uint256"
        }
      ],
      "name": "postOp",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "renounceOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "unlockStake",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "components": [
            {
              "internalType": "address",
              "name": "sender",
              "type": "address"
            },
            {
              "internalType": "uint256",
              "name": "nonce",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "initCode",
              "type": "bytes"
            },
            {
              "internalType": "bytes",
              "name": "callData",
              "type": "bytes"
            },
            {
              "internalType": "uint256",
              "name": "callGasLimit",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "verificationGasLimit",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "preVerificationGas",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "maxFeePerGas",
              "type": "uint256"
            },
            {
              "internalType": "uint256",
              "name": "maxPriorityFeePerGas",
              "type": "uint256"
            },
            {
              "internalType": "bytes",
              "name": "paymasterAndData",
              "type": "bytes"
            },
            {
              "internalType": "bytes",
              "name": "signature",
              "type": "bytes"
            }
          ],
          "internalType": "struct UserOperation",
          "name": "userOp",
          "type": "tuple"
        },
        {
          "internalType": "bytes32",
          "name": "userOpHash",
          "type": "bytes32"
        },
        {
          "internalType": "uint256",
          "name": "maxCost",
          "type": "uint256"
        }
      ],
      "name": "validatePaymasterUserOp",
      "outputs": [
        {
          "internalType": "bytes",
          "name": "context",
          "type": "bytes"
        },
        {
          "internalType": "uint256",
          "name": "validationData",
          "type": "uint256"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address payable",
          "name": "withdrawAddress",
          "type": "address"
        }
      ],
      "name": "withdrawStake",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address payable",
          "name": "withdrawAddress",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "withdrawTo",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "contract IERC20Metadata",
          "name": "token",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "target",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "withdrawTokensTo",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]

    paymaster = w3.eth.contract(address=env('paymaster_add'), abi=abi)

    exchange_rate = _get_token_rate(token)

    print('\033[96m' + "Exchange rate received." + '\033[39m')
    print(w3.eth.get_block("latest").timestamp)
    print((w3.eth.get_block("latest").number))

    paymasterData = [
        token["address"],
        1,  # SponsoringMode (GAS ONLY)
        w3.eth.get_block("latest").timestamp + 180,  # validUntil 3 minutes in the future
        0,  # Fee (in case mode == 0)
        exchange_rate,  # Exchange Rate
        b'',
    ]
    print('\033[96m' + "PaymasterData calculated" + '\033[39m')
    hash = paymaster.functions.getHash(op, paymasterData).call()
    hash = defunct_hash_message(hash)
    paymasterSigner = w3.eth.account.from_key(env('paymaster_pk'))
    sig = paymasterSigner.signHash(hash)
    paymasterData[-1] = HexBytes(sig.signature.hex())

    print('\033[96m' + "Paymaster signature signed." + '\033[39m')
    paymasterAndData = (
          str(paymasterData[0][2:])
        + str("{0:0{1}x}".format(paymasterData[1], 2))
        + str("{0:0{1}x}".format(paymasterData[2], 12))
        + str("{0:0{1}x}".format(paymasterData[3], 64))
        + str("{0:0{1}x}".format(paymasterData[4], 64))
        + sig.signature.hex()[2:]
    )

    return Success(paymasterAndData)

@method
def pm_getApprovedTokens() -> Result:
    result = []
    approved_tokens = ERC20ApprovedToken.objects.filter(chains__has_key=env('chainId'))
    print('approved_tokens',approved_tokens)
    for approvedToken in approved_tokens:
        token = approvedToken.chains[env('chainId')]
        exchange_rate = _get_token_rate(token)
        result.append({
            "address": token["address"],
            "paymaster": env('paymaster_add'),
            "exchangeRate": exchange_rate
        })
    return Success(result)

@method
def pm_chainId() -> Result:
    result = env('chainId')
    return Success(result)

@method
def pm_supportedEntryPoints() -> Result:
    result = str(env('entryPoint_add'))
    return Success(result)

def _get_token_rate(token):
    rate_request = requests.get(token["exchangeRateSource"])
    rate_float = 1 / float(re.search(r'"eth":([\d.eE-]+)', rate_request.content.decode()).group(1))
    rate = math.ceil(rate_float * (10 ** token["decimals"]))
    return rate


@csrf_exempt
def jsonrpc(request):
    return HttpResponse(
        dispatch(request.body.decode()), content_type="application/json"
    )