from eth_utils import to_checksum_address

address = "0x7D41cc4f78a68120ce74bfa82f16dce48b3c8214"  # Lowercase
checksum_address = to_checksum_address(address)
print(checksum_address)  # Verify if it matches your original input
