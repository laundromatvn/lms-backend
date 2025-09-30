# Payment Details Generation System

This document describes the payment details generation system that automatically creates QR codes and payment information after a payment is successfully created.

## Overview

The payment details generation system provides:

- **Automatic QR Code Generation**: QR codes are generated automatically after payment creation
- **Asynchronous Processing**: Uses Celery for non-blocking payment processing
- **Status Tracking**: Comprehensive payment status management
- **Error Handling**: Robust error handling with retry logic
- **Real-time Updates**: Payment status updates in real-time

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │  Celery Worker  │    │  VietQR Service │
│                 │    │                 │    │                 │
│ 1. Create       │───▶│ 2. Generate     │───▶│ 3. Generate     │
│    Payment      │    │    Details      │    │    QR Code      │
│                 │    │                 │    │                 │
│ 4. Return       │◀───│ 5. Update       │◀───│ 6. Return       │
│    Payment      │    │    Status       │    │    QR Data      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Payment Flow

### 1. Payment Creation
```http
POST /api/v1/payments/
Content-Type: application/json

{
  "order_id": "123e4567-e89b-12d3-a456-426614174000",
  "store_id": "123e4567-e89b-12d3-a456-426614174001", 
  "tenant_id": "123e4567-e89b-12d3-a456-426614174002",
  "total_amount": 100.00,
  "provider": "VIET_QR"
}
```

**Response:**
```json
{
  "id": "payment-uuid",
  "status": "NEW",
  "total_amount": 100.00,
  "provider": "VIET_QR",
  "created_at": "2024-01-01T10:00:00Z"
}
```

### 2. Automatic Task Trigger
After payment creation, a Celery task is automatically triggered:
- Task: `app.tasks.payment.generate_payment_details`
- Payment status changes to `WAITING_FOR_PAYMENT_DETAIL`

### 3. QR Code Generation
The task generates payment details:
- Calls VietQR API to generate QR code
- Updates payment with QR code and transaction details
- Payment status changes to `WAITING_FOR_PURCHASE`

### 4. Status Monitoring
Check payment status:
```http
GET /api/v1/payments/{payment_id}/status
```

**Response:**
```json
{
  "payment_id": "payment-uuid",
  "status": "WAITING_FOR_PURCHASE",
  "total_amount": 100.00,
  "provider": "VIET_QR",
  "provider_transaction_id": "vietqr-tx-id",
  "details": {
    "qr_code": "00020101021238570010A000000727012700069704080108QRIBFTTA53037045802VN6304...",
    "transaction_id": "vietqr-tx-id",
    "transaction_ref_id": "vietqr-ref-id",
    "generated_at": "2024-01-01T10:00:30Z",
    "expires_at": "2024-01-01T10:15:30Z",
    "provider": "VIET_QR",
    "amount": 100.0,
    "order_id": "order-uuid",
    "store_id": "store-uuid",
    "tenant_id": "tenant-uuid"
  },
  "is_processing": false,
  "is_ready_for_payment": true,
  "is_completed": false,
  "is_failed": false,
  "is_cancelled": false
}
```

## Payment Statuses

| Status | Description | Next Possible Statuses |
|--------|-------------|----------------------|
| `NEW` | Payment created, waiting for details generation | `WAITING_FOR_PAYMENT_DETAIL`, `CANCELLED` |
| `WAITING_FOR_PAYMENT_DETAIL` | Generating QR code and payment details | `WAITING_FOR_PURCHASE`, `FAILED`, `CANCELLED` |
| `WAITING_FOR_PURCHASE` | QR code generated, waiting for customer payment | `SUCCESS`, `FAILED`, `CANCELLED` |
| `SUCCESS` | Payment completed successfully | - |
| `FAILED` | Payment failed | `NEW` (retry) |
| `CANCELLED` | Payment cancelled | - |

## Components

### 1. PaymentOperation.generate_payment_details()

**Location:** `app/operations/payment/payment_operation.py`

**Purpose:** Generates payment details including QR code

**Features:**
- Validates payment status
- Updates payment status to `WAITING_FOR_PAYMENT_DETAIL`
- Generates QR code via VietQR service
- Updates payment with generated details
- Handles errors and status updates

### 2. Celery Task: generate_payment_details

**Location:** `app/tasks/payment/payment_tasks.py`

**Purpose:** Asynchronous payment details generation

**Features:**
- Retry logic with exponential backoff (max 3 retries)
- Comprehensive error handling
- Structured logging
- Task result tracking

### 3. PaymentService

**Location:** `app/services/payment_service.py`

**Purpose:** Payment provider integration

**Features:**
- VietQR integration
- Provider abstraction
- QR code generation

### 4. API Endpoints

**Location:** `app/apis/v1/payment.py`

**Endpoints:**
- `POST /api/v1/payments/` - Create payment (triggers task)
- `GET /api/v1/payments/{id}` - Get payment details
- `GET /api/v1/payments/{id}/status` - Get payment status

## Configuration

### Environment Variables

```bash
# VietQR Configuration
VIETQR_BASE_URL=https://dev.vietqr.org
VIETQR_USERNAME=your-username
VIETQR_PASSWORD=your-password
VIETQR_BANK_ACCOUNT=your-bank-account
VIETQR_BANK_CODE=your-bank-code
VIETQR_USER_BANK_NAME=your-bank-name

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
```

### Celery Configuration

The system uses the existing Celery configuration in `app/core/celery_app.py`:
- Broker: Redis
- Result Backend: Redis
- Task Serialization: JSON
- Timezone: Asia/Ho_Chi_Minh

## Error Handling

### 1. Validation Errors
- Invalid payment status
- Missing payment
- Invalid payment ID

### 2. External Service Errors
- VietQR API failures
- Network timeouts
- Authentication errors

### 3. Retry Logic
- Maximum 3 retries
- Exponential backoff: 60s, 120s, 240s
- Payment status updated to `FAILED` on max retries

### 4. Error Responses

**Validation Error:**
```json
{
  "success": false,
  "payment_id": "payment-uuid",
  "error": "validation_error",
  "message": "Payment cannot generate details in status SUCCESS"
}
```

**Max Retries Exceeded:**
```json
{
  "success": false,
  "payment_id": "payment-uuid", 
  "error": "max_retries_exceeded",
  "message": "Payment details generation failed after 3 retries: Connection timeout"
}
```

## Monitoring

### 1. Logging
Structured logging with `structlog`:
```python
logger.info("Starting payment details generation", payment_id=payment_id)
logger.info("Payment details generated successfully", 
           payment_id=payment_id, 
           status=payment.status.value,
           transaction_id=payment.provider_transaction_id)
logger.error("Payment details generation failed", 
            payment_id=payment_id, 
            error=str(e),
            retry_count=self.request.retries)
```

### 2. Task Monitoring
- Task status tracking
- Retry count monitoring
- Execution time tracking
- Error rate monitoring

### 3. Payment Status Tracking
- Status transition logging
- Processing time metrics
- Success/failure rates

## Testing

### 1. Unit Tests
Test individual components:
- PaymentOperation methods
- PaymentService functionality
- Task execution

### 2. Integration Tests
Test complete flow:
- Payment creation → Task trigger → QR generation → Status update

### 3. Test Script
Run the test script:
```bash
python test_payment_details_generation.py
```

## Usage Examples

### 1. Create Payment and Monitor Status

```python
import requests
import time

# Create payment
response = requests.post("http://localhost:8000/api/v1/payments/", json={
    "order_id": "order-uuid",
    "store_id": "store-uuid", 
    "tenant_id": "tenant-uuid",
    "total_amount": 100.00,
    "provider": "VIET_QR"
})

payment = response.json()
payment_id = payment["id"]

# Monitor status
while True:
    status_response = requests.get(f"http://localhost:8000/api/v1/payments/{payment_id}/status")
    status = status_response.json()
    
    print(f"Status: {status['status']}")
    
    if status["is_ready_for_payment"]:
        print(f"QR Code: {status['details']['qr_code']}")
        break
    elif status["is_failed"]:
        print("Payment details generation failed")
        break
    
    time.sleep(2)
```

### 2. Check Task Status

```python
from app.core.celery_app import celery_app

# Get task result
task_id = "celery-task-id"
result = celery_app.AsyncResult(task_id)

print(f"Task Status: {result.status}")
print(f"Task Result: {result.result}")
```

## Troubleshooting

### 1. Common Issues

#### Task Not Executing
```bash
# Check Celery worker status
celery -A app.core.celery_app inspect active

# Check Redis connection
redis-cli ping
```

#### QR Generation Failing
```bash
# Check VietQR credentials
echo $VIETQR_USERNAME
echo $VIETQR_PASSWORD

# Test VietQR API manually
curl -X POST "https://dev.vietqr.org/vqr/api/token_generate" \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'
```

#### Payment Status Not Updating
```bash
# Check database connection
python -c "from app.libs.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check payment in database
python -c "from app.operations.payment.payment_operation import PaymentOperation; print(PaymentOperation.get_payment_by_id('payment-uuid'))"
```

### 2. Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
celery -A app.core.celery_app worker --loglevel=debug
```

### 3. Manual Task Execution

Execute task manually for testing:
```python
from app.tasks.payment.payment_tasks import generate_payment_details

result = generate_payment_details.delay("payment-uuid")
print(result.get())
```

## Performance Considerations

### 1. Task Concurrency
- Default: 4 concurrent workers
- Adjust based on VietQR API limits
- Monitor API rate limits

### 2. QR Code Expiration
- Default: 15 minutes
- Configurable via environment variables
- Automatic cleanup of expired payments

### 3. Database Performance
- Indexed payment status queries
- Efficient status updates
- Connection pooling

## Security

### 1. API Security
- JWT authentication required
- Payment access validation
- User permission checks

### 2. Data Protection
- QR codes contain no sensitive data
- Transaction IDs are provider-generated
- No payment card information stored

### 3. Network Security
- HTTPS for VietQR API calls
- Secure Redis connections
- Environment variable protection

## Future Enhancements

### 1. Multiple Payment Providers
- Support for additional QR providers
- Provider selection logic
- Fallback mechanisms

### 2. Webhook Support
- Payment completion webhooks
- Real-time status updates
- Event-driven architecture

### 3. Analytics
- Payment success rates
- Processing time metrics
- Provider performance tracking

### 4. Caching
- QR code caching
- Payment status caching
- Redis-based caching layer
