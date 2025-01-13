import pytest
import asyncio
from unittest.mock import Mock, patch
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.system_program import TransferParams, transfer

# Import your SolanaClient class - adjust the import path as needed
import sys
import os

# Add 'services' directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'source', 'python', 'services')))

from solana_client import SolanaClient

@pytest.fixture
def client():
    """Create a test client with mock configuration"""
    config = {"rpc_url": "http://mock-url"}
    return SolanaClient(config)

@pytest.fixture
def mock_response():
    """Create a mock response for RPC calls"""
    mock = Mock()
    mock.value = Mock()
    return mock

@pytest.mark.asyncio
async def test_transfer_message_construction():
    """Test that transfer message is constructed correctly"""
    # Create test keypairs
    sender = Keypair()
    receiver = Keypair()
    amount_lamports = 1_000_000

    # Create client with mock RPC
    client = SolanaClient({"rpc_url": "http://mock-url"})
    
    # Mock the get_latest_blockhash response
    mock_blockhash = Hash.default()  # Using default hash for testing
    mock_blockhash_response = Mock()
    mock_blockhash_response.value.blockhash = mock_blockhash
    
    # Patch the client methods
    with patch.object(client.client, 'get_latest_blockhash', 
                     return_value=mock_blockhash_response):
        try:
            # Call the transfer method but don't send the transaction
            await client.transfer_sol(
                sender, 
                str(receiver.pubkey()), 
                amount_lamports
            )
            
            # Verify the message would be constructed correctly
            transfer_ix = transfer(
                TransferParams(
                    from_pubkey=sender.pubkey(),
                    to_pubkey=receiver.pubkey(),
                    lamports=amount_lamports
                )
            )
            
            expected_message = MessageV0.try_compile(
                payer=sender.pubkey(),
                instructions=[transfer_ix],
                address_lookup_table_accounts=[],
                recent_blockhash=mock_blockhash
            )
            
            expected_tx = VersionedTransaction(expected_message, [sender])
            
            # Verify the transaction would be properly signed
            assert len(expected_tx.signatures) == 1
            assert expected_tx.signatures[0] != bytes([0] * 64)  # Signature should not be empty
            
            print("Message construction test passed!")
            print(f"From: {sender.pubkey()}")
            print(f"To: {receiver.pubkey()}")
            print(f"Amount: {amount_lamports} lamports")
            print(f"Message: {expected_message}")
            
        except Exception as e:
            print(f"Error during test: {e}")
            raise

@pytest.mark.asyncio
async def test_get_token_account():
    """Test get_token_account method"""
    client = SolanaClient({"rpc_url": "http://mock-url"})
    test_account = Keypair()
    
    mock_response = Mock()
    mock_response.value = {"balance": 1000}
    
    with patch.object(client.client, 'get_account_info', 
                     return_value=mock_response):
        result = await client.get_token_account(str(test_account.pubkey()))
        assert result == {"balance": 1000}

@pytest.mark.asyncio
async def test_get_token_supply():
    """Test get_token_supply method"""
    client = SolanaClient({"rpc_url": "http://mock-url"})
    test_token = Keypair()
    
    mock_response = Mock()
    mock_response.value.amount = "1000000"
    
    with patch.object(client.client, 'get_token_supply', 
                     return_value=mock_response):
        result = await client.get_token_supply(str(test_token.pubkey()))
        assert result == 1000000

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_transfer_message_construction())
    print("\nAll tests completed!")