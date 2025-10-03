# Configuration

Auris Tools uses a central configuration system to manage AWS credentials and settings.

## AWSConfiguration Class

The `AWSConfiguration` class is the core configuration component for AWS services. It handles:

- AWS credentials management
- Region configuration
- Session management
- Client-specific configurations

## Basic Usage

```python
from auris_tools.configuration import AWSConfiguration

# Create a configuration using environment variables or AWS configuration files
config = AWSConfiguration()

# Create a configuration with explicit parameters
config = AWSConfiguration(
    region="us-west-2",
    profile_name="my-aws-profile",
    access_key_id="YOUR_ACCESS_KEY",
    secret_access_key="YOUR_SECRET_KEY"
)
```

## Environment Variables

Auris Tools will automatically use the following environment variables if available:

- `AWS_REGION` - The AWS region to use
- `AWS_PROFILE` - The AWS profile name to use
- `AWS_ACCESS_KEY_ID` - AWS access key ID
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key

## Configuration Precedence

The configuration system follows this precedence order:

1. Explicitly provided parameters in the constructor
2. Environment variables
3. AWS configuration files (~/.aws/credentials and ~/.aws/config)
4. Instance metadata (for EC2 instances)