# Azure Resources for Amora Sync

This document outlines the Azure resources required for implementing the Amora Sync real-time communication architecture.

## MQTT Broker Options in Azure

### Option 1: EMQX on Azure Container Apps (Recommended)

EMQX is an open-source, highly scalable MQTT broker that can be deployed on Azure Container Apps.

**Resources Required:**
- **Azure Container Apps Environment**
  - SKU: Consumption or Dedicated
  - Min replicas: 2
  - Max replicas: 10
  - CPU: 2 cores per replica
  - Memory: 4 GB per replica
  
- **Azure Container Registry**
  - SKU: Standard
  - Used to store EMQX container images
  
- **Azure Database for PostgreSQL**
  - SKU: General Purpose, 4 vCores
  - Storage: 100 GB
  - Used for EMQX authentication and session persistence
  
- **Azure Cache for Redis**
  - SKU: Standard C1
  - Used for EMQX session state and message caching
  
- **Azure Key Vault**
  - SKU: Standard
  - Used to store TLS certificates and secrets
  
- **Azure DNS Zone**
  - For custom domain (mqtt.amora.example.com)
  
- **Azure Front Door**
  - SKU: Standard
  - Used for global load balancing and TLS termination

**Estimated Monthly Cost:** $500-800

### Option 2: HiveMQ on Azure Kubernetes Service

HiveMQ is a commercial MQTT broker with enterprise features that can be deployed on AKS.

**Resources Required:**
- **Azure Kubernetes Service**
  - Node count: 3-5
  - VM size: Standard_D4s_v3
  - Disk: 128 GB Premium SSD
  
- **Azure Database for PostgreSQL**
  - SKU: General Purpose, 4 vCores
  - Storage: 100 GB
  
- **Azure Storage Account**
  - SKU: Standard LRS
  - Used for persistent storage
  
- **Azure Key Vault**
  - SKU: Standard
  
- **Azure DNS Zone**
  - For custom domain
  
- **Azure Application Gateway**
  - SKU: Standard V2
  - Used for load balancing and TLS termination

**Estimated Monthly Cost:** $800-1,200 (plus HiveMQ license)

### Option 3: VerneMQ on Azure VMs

VerneMQ is an open-source MQTT broker that can be deployed on Azure VMs.

**Resources Required:**
- **Azure Virtual Machines**
  - Count: 3-5
  - Size: Standard_D4s_v3
  - Disk: 128 GB Premium SSD
  
- **Azure Load Balancer**
  - SKU: Standard
  
- **Azure Database for PostgreSQL**
  - SKU: General Purpose, 4 vCores
  - Storage: 100 GB
  
- **Azure Key Vault**
  - SKU: Standard
  
- **Azure DNS Zone**
  - For custom domain

**Estimated Monthly Cost:** $600-1,000

## Monitoring and Logging Resources

- **Azure Monitor**
  - Used for monitoring MQTT broker metrics
  - Custom metrics for connection count, message throughput, etc.
  
- **Log Analytics Workspace**
  - SKU: Pay-as-you-go
  - Retention: 30 days
  - Used for centralized logging
  
- **Application Insights**
  - Used for SDK performance monitoring
  
- **Azure Dashboard**
  - Custom dashboard for MQTT broker monitoring

**Estimated Monthly Cost:** $100-200

## Security Resources

- **Azure AD B2C**
  - SKU: Consumption-based
  - Used for client application authentication
  - Custom policies for user authentication
  
- **Azure Key Vault**
  - SKU: Standard
  - Used for certificate and secret management
  
- **Azure Private Link**
  - Used for private connectivity to Azure services
  
- **Azure DDoS Protection**
  - SKU: Standard
  - Used for DDoS protection

**Estimated Monthly Cost:** $100-300

## Deployment Resources

- **Azure DevOps**
  - SKU: Basic
  - Used for CI/CD pipelines
  
- **Azure Container Registry**
  - SKU: Standard
  - Used for container image storage
  
- **Azure Resource Manager Templates**
  - Used for infrastructure as code

**Estimated Monthly Cost:** $50-100

## Total Estimated Monthly Cost

- **Option 1 (EMQX on Azure Container Apps):** $750-1,400
- **Option 2 (HiveMQ on AKS):** $1,050-1,800 (plus HiveMQ license)
- **Option 3 (VerneMQ on Azure VMs):** $850-1,600

## Scaling Considerations

- **Connection Scaling:**
  - Each MQTT connection requires memory and a file descriptor
  - Plan for 1-2 MB of memory per connection
  - Scale horizontally for more connections
  
- **Message Throughput Scaling:**
  - Message throughput depends on message size and QoS level
  - Plan for 1,000-5,000 messages per second per core
  - Scale vertically for higher throughput
  
- **Storage Scaling:**
  - Message persistence requires storage
  - Plan for 1-10 GB of storage per million messages
  - Scale storage based on retention requirements

## High Availability Design

- **Multi-Zone Deployment:**
  - Deploy MQTT broker across multiple availability zones
  - Use zone-redundant services for dependencies
  
- **Failover Mechanism:**
  - Implement automatic failover for MQTT broker
  - Use Azure Traffic Manager for global failover
  
- **Backup and Recovery:**
  - Regular backups of configuration and data
  - Disaster recovery plan with RTO and RPO targets

## Deployment Template

A sample ARM template for deploying the recommended EMQX on Azure Container Apps solution is available in the `infrastructure` directory.

## Next Steps

1. Select the preferred MQTT broker option
2. Create a detailed cost estimate
3. Create infrastructure as code templates
4. Set up CI/CD pipelines for deployment
5. Implement monitoring and alerting
