# VietQR Token Generation API

## Overview

This API endpoint allows VietQR partners to generate access tokens for authenticating with the LMS system for transaction synchronization.

## Endpoint

**POST** `/vietqr/api/token_generate`

## Authentication

The endpoint uses Basic Authentication with VietQR partner credentials.

### Headers

```
Content-Type: application/json
Authorization: Basic <base64_encoded_credentials>
```

Where `<base64_encoded_credentials>` is the base64 encoding of `username:password`.

## Request

### Request Body

The request body is empty as per VietQR API specification.

```json
{}
```

## Response

### Success Response (200 OK)

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 300
}
```

### Response Fields

- `access_token` (string, required): Bearer token for authenticating with LMS APIs
- `token_type` (string, required): Token type, always "Bearer"
- `expires_in` (integer, required): Token expiration time in seconds (default: 300 seconds = 5 minutes)

### Error Responses

#### 401 Unauthorized
```json
{
    "detail": "Invalid VietQR partner credentials"
}
```

#### 500 Internal Server Error
```json
{
    "detail": "Internal server error while generating token"
}
```

## Configuration

The following environment variables need to be configured:

```bash
# VietQR Partner Credentials
BACKEND_VIETQR_PARTNER_USERNAME=your-vietqr-partner-username
BACKEND_VIETQR_PARTNER_PASSWORD=your-vietqr-partner-password

# Token Expiration (optional, default: 300 seconds)
BACKEND_VIETQR_TOKEN_EXPIRE_SECONDS=300
```

## Usage Example

### cURL

```bash
curl -X POST "https://your-lms-host/vietqr/api/token_generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'username:password' | base64)" \
  -d '{}'
```

### Python

```python
import requests
import base64

# Encode credentials
credentials = base64.b64encode(b'username:password').decode('utf-8')

# Make request
response = requests.post(
    'https://your-lms-host/vietqr/api/token_generate',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Basic {credentials}'
    },
    json={}
)

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    expires_in = token_data['expires_in']
    print(f"Token: {access_token}")
    print(f"Expires in: {expires_in} seconds")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## Security Notes

1. The generated token contains specific claims for VietQR partner identification
2. Tokens have a short expiration time (5 minutes by default) for security
3. Basic Authentication credentials should be kept secure and rotated regularly
4. The token can be used to authenticate with other LMS APIs that require VietQR partner access

## Token Claims

The generated JWT token contains the following claims:

```json
{
    "vietqr_partner": true,
    "username": "partner-username",
    "purpose": "transaction_sync",
    "exp": 1234567890
}
```

These claims can be used to identify and authorize VietQR partner requests in other API endpoints.
