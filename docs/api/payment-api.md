# Payment API Documentation

## Overview

The Payment API provides comprehensive endpoints for managing payments, including initialization, status checking, QR code generation, and integration with the order system.

## Base URL

```
/api/v1/payments
```

## Authentication

All endpoints require authentication. Include the authentication token in the request headers:

```http
Authorization: Bearer <your-token>
```

## Payment Endpoints

### Initialize Payment

Creates a new payment for an order.

**Endpoint:** `POST /api/v1/payments/initialize`

**Request Body:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_id": "550e8400-e29b-41d4-a716-446655440001",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440002",
  "total_amount": 25.50,
  "provider": "VIET_QR"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:30:00Z",
  "status": "NEW",
  "details": null,
  "store_id": "550e8400-e29b-41d4-a716-446655440001",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440002",
  "total_amount": 25.50,
  "provider": "VIET_QR",
  "provider_transaction_id": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data or validation errors
- `404 Not Found` - Order, store, or tenant not found
- `409 Conflict` - Order already has an active payment transaction

### Get Payment

Retrieves a payment by ID.

**Endpoint:** `GET /api/v1/payments/{payment_id}`

**Path Parameters:**
- `payment_id` (UUID) - The payment ID

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:35:00Z",
  "status": "WAITING_FOR_PURCHASE",
  "details": {
    "qr_code": "00020101021238570010A000000727012700069704080108QRIBFTTA53037045802VN6304A1B2",
    "qr_image_url": "https://api.vietqr.io/v2/generate/...",
    "expired_at": "2025-01-27T16:00:00Z",
    "payment_instructions": "Scan QR code to complete payment",
    "transaction_id": "vietqr_txn_123456",
    "transaction_ref_id": "ref_789012"
  },
  "store_id": "550e8400-e29b-41d4-a716-446655440001",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440002",
  "total_amount": 25.50,
  "provider": "VIET_QR",
  "provider_transaction_id": "vietqr_txn_123456"
}
```

**Error Responses:**
- `404 Not Found` - Payment not found

## Customer UI Integration Flow

### Complete Payment Flow Example

1. **Initialize Payment:**
```bash
curl -X POST "https://api.lms.com/api/v1/payments/initialize" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "store_id": "550e8400-e29b-41d4-a716-446655440001",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440002",
    "total_amount": 25.50,
    "provider": "VIET_QR"
  }'
```

2. **Check Payment Detail Status (Polling):**
```bash
curl -X GET "https://api.lms.com/api/v1/payments/550e8400-e29b-41d4-a716-446655440003/details/status" \
  -H "Authorization: Bearer <token>"
```

3. **Get Payment Details (when ready):**
```bash
curl -X GET "https://api.lms.com/api/v1/payments/550e8400-e29b-41d4-a716-446655440003/details" \
  -H "Authorization: Bearer <token>"
```

4. **Check Payment Status (Polling):**
```bash
curl -X GET "https://api.lms.com/api/v1/payments/550e8400-e29b-41d4-a716-446655440003/details/status" \
  -H "Authorization: Bearer <token>"
```

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate payment)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Validation Errors

When validation fails, the API returns detailed error information:

```json
{
  "detail": [
    {
      "loc": ["body", "total_amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Payment Initialization**: 5 requests per minute per user
- **Status Checking**: 30 requests per minute per user
- **General Endpoints**: 100 requests per minute per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## SDK Examples

### Python

```python
import requests
import time

# Initialize payment
response = requests.post(
    "https://api.lms.com/api/v1/payments/initialize",
    headers={"Authorization": "Bearer <token>"},
    json={
        "order_id": "550e8400-e29b-41d4-a716-446655440000",
        "store_id": "550e8400-e29b-41d4-a716-446655440001",
        "tenant_id": "550e8400-e29b-41d4-a716-446655440002",
        "total_amount": 25.50,
        "provider": "VIET_QR"
    }
)

payment = response.json()
payment_id = payment["id"]

# Poll for payment details
while True:
    status_response = requests.get(
        f"https://api.lms.com/api/v1/payments/{payment_id}/details/status",
        headers={"Authorization": "Bearer <token>"}
    )
    status = status_response.json()
    
    if status["is_ready"]:
        break
    
    time.sleep(2)  # Wait 2 seconds before next poll

# Get payment details
details_response = requests.get(
    f"https://api.lms.com/api/v1/payments/{payment_id}/details",
    headers={"Authorization": "Bearer <token>"}
)
details = details_response.json()

print(f"QR Code: {details['qr_code']}")
print(f"Amount: {details['amount']} {details['currency']}")

# Poll for payment completion
while True:
    status_response = requests.get(
        f"https://api.lms.com/api/v1/payments/{payment_id}/details/status",
        headers={"Authorization": "Bearer <token>"}
    )
    status = status_response.json()
    
    if status["is_completed"]:
        if status["status"] == "SUCCESS":
            print("Payment completed successfully!")
        else:
            print(f"Payment failed: {status['status']}")
        break
    
    time.sleep(3)  # Wait 3 seconds before next poll
```

### JavaScript

```javascript
// Initialize payment
const initResponse = await fetch('https://api.lms.com/api/v1/payments/initialize', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    order_id: '550e8400-e29b-41d4-a716-446655440000',
    store_id: '550e8400-e29b-41d4-a716-446655440001',
    tenant_id: '550e8400-e29b-41d4-a716-446655440002',
    total_amount: 25.50,
    provider: 'VIET_QR'
  })
});

const payment = await initResponse.json();
const paymentId = payment.id;

// Poll for payment details
const pollForDetails = async () => {
  while (true) {
    const statusResponse = await fetch(
      `https://api.lms.com/api/v1/payments/${paymentId}/details/status`,
      {
        headers: {
          'Authorization': 'Bearer <token>'
        }
      }
    );
    const status = await statusResponse.json();
    
    if (status.is_ready) {
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
  }
};

await pollForDetails();

// Get payment details
const detailsResponse = await fetch(
  `https://api.lms.com/api/v1/payments/${paymentId}/details`,
  {
    headers: {
      'Authorization': 'Bearer <token>'
    }
  }
);
const details = await detailsResponse.json();

console.log(`QR Code: ${details.qr_code}`);
console.log(`Amount: ${details.amount} ${details.currency}`);

// Poll for payment completion
const pollForCompletion = async () => {
  while (true) {
    const statusResponse = await fetch(
      `https://api.lms.com/api/v1/payments/${paymentId}/details/status`,
      {
        headers: {
          'Authorization': 'Bearer <token>'
        }
      }
    );
    const status = await statusResponse.json();
    
    if (status.is_completed) {
      if (status.status === 'SUCCESS') {
        console.log('Payment completed successfully!');
      } else {
        console.log(`Payment failed: ${status.status}`);
      }
      break;
    }
    
    await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds
  }
};

await pollForCompletion();
```

## Webhook Integration

### Payment Status Webhook

The system can send webhooks when payment status changes:

**Webhook URL:** `POST /api/v1/payments/webhook`

**Payload:**
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "SUCCESS",
  "transaction_id": "vietqr_txn_123456",
  "amount": 25.50,
  "currency": "VND",
  "timestamp": "2025-01-27T15:45:00Z"
}
```

## Best Practices

### Customer UI Implementation

1. **Initialize Payment**: Call the initialize endpoint when user confirms order
2. **Poll for Details**: Continuously poll the details/status endpoint until `is_ready` is true
3. **Display QR Code**: Show QR code and payment instructions to customer
4. **Poll for Completion**: Continuously poll the details/status endpoint until `is_completed` is true
5. **Handle Results**: Show success or failure message based on final status

### Error Handling

1. **Network Errors**: Implement retry logic with exponential backoff
2. **Timeout Handling**: Set appropriate timeouts for polling operations
3. **User Feedback**: Provide clear error messages to users
4. **Fallback Options**: Allow users to retry failed payments

### Performance Optimization

1. **Polling Intervals**: Use appropriate polling intervals (2-3 seconds)
2. **Caching**: Cache payment details to avoid repeated API calls
3. **Connection Reuse**: Reuse HTTP connections for polling requests
4. **Timeout Management**: Set reasonable timeouts for long-running operations
