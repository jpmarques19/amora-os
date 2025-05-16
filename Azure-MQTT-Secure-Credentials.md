# Azure MQTT Secure Credentials Management

This document provides guidance on securely managing Azure credentials when using remote agents and AI-assisted coding, including implementation guidance for GitHub Secrets and other secure credential storage solutions.

## Secure Credential Management Approaches

### Challenges with Remote Development

When working with remote agents, AI-assisted coding, and CI/CD pipelines, several security challenges arise:

1. **Credential Exposure**: Credentials should never be hardcoded or exposed in code repositories
2. **Access Control**: Only authorized systems and users should have access to credentials
3. **Credential Rotation**: Credentials should be rotatable without code changes
4. **Least Privilege**: Services should only have access to the minimum required permissions
5. **Audit Trail**: Access to credentials should be logged and auditable

### Recommended Approaches

| Approach | Use Case | Pros | Cons |
|----------|----------|------|------|
| **Environment Variables** | Local development | Simple to implement | Not suitable for production |
| **GitHub Secrets** | CI/CD pipelines | Integrated with GitHub Actions | Limited to GitHub ecosystem |
| **Azure Key Vault** | Production systems | Highly secure, access control | More complex setup |
| **Managed Identities** | Azure resources | No stored credentials | Limited to Azure resources |
| **Azure DevOps Variable Groups** | Azure DevOps pipelines | Integrated with Azure DevOps | Limited to Azure DevOps |

## GitHub Secrets Implementation

GitHub Secrets provides a secure way to store sensitive information in your GitHub repositories, making it ideal for CI/CD pipelines and remote development scenarios.

### Setting Up GitHub Secrets

1. **Navigate to Repository Settings**
   - Go to your GitHub repository
   - Click on "Settings" tab
   - Select "Secrets and variables" from the left sidebar
   - Click on "Actions"

2. **Add New Repository Secret**
   - Click "New repository secret"
   - Enter a name for your secret (e.g., `AZURE_IOT_HUB_CONNECTION_STRING`)
   - Paste the value (e.g., your IoT Hub connection string)
   - Click "Add secret"

3. **Add Multiple Secrets**
   For a complete setup, add the following secrets:
   - `AZURE_IOT_HUB_CONNECTION_STRING`: IoT Hub connection string
   - `AZURE_IOT_DEVICE_CONNECTION_STRING`: Device connection string
   - `AZURE_IOT_DEVICE_KEY`: Device primary key
   - `AZURE_IOT_HUB_NAME`: IoT Hub name
   - `AZURE_RESOURCE_GROUP`: Resource group name
   - `AZURE_SUBSCRIPTION_ID`: Azure subscription ID

### Using GitHub Secrets in GitHub Actions

```yaml
name: IoT Device Simulation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  run-simulation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install azure-iot-device
    
    - name: Run device simulation
      env:
        IOT_HUB_CONNECTION_STRING: ${{ secrets.AZURE_IOT_HUB_CONNECTION_STRING }}
        IOT_DEVICE_CONNECTION_STRING: ${{ secrets.AZURE_IOT_DEVICE_CONNECTION_STRING }}
      run: |
        python scripts/device_simulation.py
```

### Accessing GitHub Secrets in Code

In the GitHub Actions environment, secrets are exposed as environment variables:

```python
import os
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message

async def main():
    # Get connection string from environment variable
    conn_str = os.environ.get("IOT_DEVICE_CONNECTION_STRING")
    if not conn_str:
        raise ValueError("Connection string not found in environment variables")
    
    # Create client
    client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    
    # Connect and send message
    await client.connect()
    await client.send_message(Message("Test message from GitHub Actions"))
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Azure Key Vault Implementation

For production environments, Azure Key Vault provides a more robust solution for credential management.

### Setting Up Azure Key Vault

1. **Create Key Vault**

```bash
# Set variables
RESOURCE_GROUP="iot-production-rg"
LOCATION="eastus"
KEY_VAULT_NAME="iot-credentials-kv"

# Create Key Vault
az keyvault create \
  --name $KEY_VAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku standard
```

2. **Store Credentials in Key Vault**

```bash
# Store IoT Hub connection string
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "IoTHubConnectionString" \
  --value "HostName=your-iothub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=your-key"

# Store device connection string
az keyvault secret set \
  --vault-name $KEY_VAULT_NAME \
  --name "DeviceConnectionString" \
  --value "HostName=your-iothub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-device-key"
```

3. **Set Access Policies**

```bash
# Get the object ID of the service principal or user
OBJECT_ID=$(az ad signed-in-user show --query objectId -o tsv)

# Set access policy
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $OBJECT_ID \
  --secret-permissions get list set delete
```

### Accessing Key Vault from Code

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.iot.device import IoTHubDeviceClient, Message

def get_device_connection_string():
    # Key Vault URL
    key_vault_url = f"https://iot-credentials-kv.vault.azure.net/"
    
    # Create credential
    credential = DefaultAzureCredential()
    
    # Create client
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    
    # Get secret
    secret = client.get_secret("DeviceConnectionString")
    
    return secret.value

def send_telemetry():
    # Get connection string from Key Vault
    conn_str = get_device_connection_string()
    
    # Create IoT Hub client
    client = IoTHubDeviceClient.create_from_connection_string(conn_str)
    
    # Connect to IoT Hub
    client.connect()
    
    # Send message
    client.send_message(Message("Test message"))
    
    # Disconnect
    client.disconnect()

if __name__ == "__main__":
    send_telemetry()
```

### Integrating Key Vault with GitHub Actions

```yaml
name: IoT Device Simulation with Key Vault

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  run-simulation:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install azure-identity azure-keyvault-secrets azure-iot-device
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Run device simulation
      env:
        KEY_VAULT_NAME: iot-credentials-kv
      run: |
        python scripts/device_simulation_keyvault.py
```

## Managed Identities Implementation

Managed Identities eliminate the need to store credentials by providing Azure resources with an automatically managed identity in Azure AD.

### Setting Up Managed Identity

1. **Create a User-Assigned Managed Identity**

```bash
# Create managed identity
az identity create \
  --name iot-device-identity \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

2. **Assign Roles to the Managed Identity**

```bash
# Get identity client ID
IDENTITY_CLIENT_ID=$(az identity show \
  --name iot-device-identity \
  --resource-group $RESOURCE_GROUP \
  --query clientId -o tsv)

# Get IoT Hub resource ID
IOT_HUB_ID=$(az iot hub show \
  --name your-iothub \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Assign IoT Hub Data Contributor role
az role assignment create \
  --assignee $IDENTITY_CLIENT_ID \
  --role "IoT Hub Data Contributor" \
  --scope $IOT_HUB_ID
```

3. **Assign Key Vault Access Policy**

```bash
# Get identity principal ID
IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name iot-device-identity \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)

# Set Key Vault access policy
az keyvault set-policy \
  --name $KEY_VAULT_NAME \
  --object-id $IDENTITY_PRINCIPAL_ID \
  --secret-permissions get list
```

### Using Managed Identity in Code

```python
from azure.identity import ManagedIdentityCredential
from azure.iot.hub import IoTHubRegistryManager

def register_device():
    # Create credential using managed identity
    credential = ManagedIdentityCredential(client_id="your-managed-identity-client-id")
    
    # IoT Hub endpoint
    iot_hub_name = "your-iothub"
    endpoint = f"https://{iot_hub_name}.azure-devices.net"
    
    # Create IoT Hub Registry Manager with token credential
    registry_manager = IoTHubRegistryManager(endpoint, credential)
    
    # Register a new device
    device_id = "new-device-001"
    primary_key = "your-device-key"  # Optional, will be generated if not provided
    
    device = registry_manager.create_device_with_sas(device_id, primary_key, secondary_key=None)
    
    print(f"Device created: {device.device_id}")
    return device

if __name__ == "__main__":
    register_device()
```

## Development Workflow Changes

To securely manage Azure credentials in your development workflow, consider the following changes:

### Local Development

1. **Use .env Files with .gitignore**
   - Create a `.env` file for local development
   - Add the file to `.gitignore` to prevent accidental commits
   - Use a package like `python-dotenv` to load environment variables

   Example `.env` file:
   ```
   IOT_HUB_CONNECTION_STRING=HostName=your-iothub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=your-key
   IOT_DEVICE_CONNECTION_STRING=HostName=your-iothub.azure-devices.net;DeviceId=your-device;SharedAccessKey=your-device-key
   ```

   Loading in Python:
   ```python
   from dotenv import load_dotenv
   import os
   
   # Load environment variables from .env file
   load_dotenv()
   
   # Access environment variables
   conn_str = os.getenv("IOT_DEVICE_CONNECTION_STRING")
   ```

2. **Use Credential Providers**
   - Implement a credential provider pattern
   - Support multiple credential sources (environment, Key Vault, etc.)

   ```python
   class CredentialProvider:
       @staticmethod
       def get_connection_string():
           # Try environment variable first
           conn_str = os.getenv("IOT_DEVICE_CONNECTION_STRING")
           if conn_str:
               return conn_str
           
           # Try Azure Key Vault
           try:
               from azure.identity import DefaultAzureCredential
               from azure.keyvault.secrets import SecretClient
               
               credential = DefaultAzureCredential()
               client = SecretClient(
                   vault_url=f"https://{os.getenv('KEY_VAULT_NAME')}.vault.azure.net/",
                   credential=credential
               )
               return client.get_secret("DeviceConnectionString").value
           except Exception as e:
               print(f"Failed to get connection string from Key Vault: {e}")
           
           raise ValueError("No connection string found")
   ```

### CI/CD Pipeline

1. **Use GitHub Actions Environment**
   - Create environments in GitHub with protection rules
   - Restrict secrets to specific environments
   - Require approvals for sensitive environments

   ```yaml
   name: IoT Device Deployment
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     deploy-dev:
       runs-on: ubuntu-latest
       environment: development
       
       steps:
       - uses: actions/checkout@v2
       - name: Deploy to Dev
         env:
           IOT_HUB_CONNECTION_STRING: ${{ secrets.AZURE_IOT_HUB_CONNECTION_STRING }}
         run: ./deploy.sh
     
     deploy-prod:
       needs: deploy-dev
       runs-on: ubuntu-latest
       environment: production
       
       steps:
       - uses: actions/checkout@v2
       - name: Deploy to Production
         env:
           IOT_HUB_CONNECTION_STRING: ${{ secrets.AZURE_IOT_HUB_CONNECTION_STRING }}
         run: ./deploy.sh
   ```

2. **Use OIDC for GitHub Actions**
   - Configure OpenID Connect (OIDC) between GitHub and Azure
   - Eliminate the need for long-lived credentials
   - Use federated credentials for secure authentication

   ```yaml
   name: Azure Login with OIDC
   
   on:
     push:
       branches: [ main ]
   
   permissions:
     id-token: write
     contents: read
   
   jobs:
     build-and-deploy:
       runs-on: ubuntu-latest
       
       steps:
       - uses: actions/checkout@v2
       
       - name: Azure login
         uses: azure/login@v1
         with:
           client-id: ${{ secrets.AZURE_CLIENT_ID }}
           tenant-id: ${{ secrets.AZURE_TENANT_ID }}
           subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
   
       - name: Run Azure CLI commands
         run: |
           az iot hub device-identity list --hub-name your-iothub
   ```

### Code Review Process

1. **Credential Scanning**
   - Implement pre-commit hooks to scan for credentials
   - Use tools like GitGuardian or GitHub Secret Scanning
   - Block commits containing credentials

2. **Review Guidelines**
   - Create guidelines for reviewing code that interacts with credentials
   - Ensure credential handling follows best practices
   - Verify that no credentials are hardcoded

### AI-Assisted Coding Considerations

When using AI-assisted coding tools with Azure credentials:

1. **Never Share Credentials with AI Tools**
   - Do not paste real credentials in prompts
   - Use placeholder values in examples
   - Sanitize code before sharing with AI tools

2. **Use Credential Placeholders**
   - Replace actual credentials with placeholders in code shared with AI
   - Example: `"HostName=<iothub-name>.azure-devices.net;DeviceId=<device-id>;SharedAccessKey=<key>"`

3. **Review AI-Generated Code**
   - Carefully review any credential handling in AI-generated code
   - Ensure AI-generated code follows security best practices
   - Modify code to use secure credential sources

4. **Educate AI Tools**
   - Provide context about your secure credential management approach
   - Instruct AI tools to follow your security practices
   - Correct AI when it suggests insecure practices

## Security Best Practices Summary

1. **Never Hardcode Credentials**
   - Always retrieve credentials from secure sources
   - Use environment variables, Key Vault, or managed identities

2. **Implement Least Privilege**
   - Use service principals with minimal required permissions
   - Create separate credentials for different environments
   - Regularly review and audit permissions

3. **Rotate Credentials Regularly**
   - Implement automated credential rotation
   - Use short-lived credentials where possible
   - Design systems to handle credential rotation without downtime

4. **Secure Credential Storage**
   - Use dedicated services for credential storage (Key Vault, GitHub Secrets)
   - Encrypt credentials at rest
   - Implement access controls for credential storage

5. **Audit and Monitor**
   - Enable logging for credential access
   - Monitor for unusual credential usage patterns
   - Implement alerts for potential credential leaks

By following these guidelines and implementing the recommended approaches, you can securely manage Azure credentials when using remote agents and AI-assisted coding, ensuring that your IoT solution remains secure throughout the development lifecycle.
