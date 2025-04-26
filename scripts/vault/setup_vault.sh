#!/bin/bash
# setup_vault.sh - Script to set up HashiCorp Vault for Hydra News

# Download and install Vault
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install vault

# Set up Vault development server
mkdir -p ~/vault-data
vault server -dev -dev-root-token-id="hydra-dev-token" > ../logs/vault.log 2>&1 &
echo $! > ../.vault_pid

# Wait for Vault to start
sleep 2

# Configure Vault for Hydra News
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='hydra-dev-token'

# Enable transit engine for encryption
vault secrets enable transit

# Create encryption keys for different components
vault write -f transit/keys/content_encryption
vault write -f transit/keys/user_identity
vault write -f transit/keys/source_protection

# Configure key rotation policies
vault write transit/keys/content_encryption/config rotation_period="30d"
vault write transit/keys/user_identity/config rotation_period="60d"
vault write transit/keys/source_protection/config rotation_period="90d"

echo "Vault setup complete. Development server running with:"
echo "VAULT_ADDR=$VAULT_ADDR"
echo "VAULT_TOKEN=$VAULT_TOKEN"
