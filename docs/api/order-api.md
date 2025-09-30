# Order API Documentation

## Overview

The Order API provides comprehensive endpoints for managing laundry orders, including creation, updates, status management, and integration with payment and machine systems.

## Base URL

```
/api/v1/order
```

## Authentication

All endpoints require authentication. Include the authentication token in the request headers:

```http
Authorization: Bearer <your-token>
```

## Order Management Endpoints

### Create Order

Creates a new order with machine selections.

**Endpoint:** `POST /api/v1/order/`

**Request Body:**
```json
{
  "store_id": "550e8400-e29b-41d4-a716-446655440000",
  "machine_selections": [
    {
      "machine_id": "550e8400-e29b-41d4-a716-446655440001",
      "add_ons": [
        {
          "type": "DETERGENT",
          "price": 5000.00,
          "is_default": false,
          "quantity": 1
        },
        {
          "type": "SOFTENER",
          "price": 3000.00,
          "is_default": false,
          "quantity": 1
        },
        {
          "type": "HOT_WATER",
          "price": 2000.00,
          "is_default": true,
          "quantity": 1
        }
      ]
    },
    {
      "machine_id": "550e8400-e29b-41d4-a716-446655440002",
      "add_ons": null
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:30:00Z",
  "status": "WAITING_FOR_PAYMENT",
  "total_amount": 25.50,
  "total_washer": 1,
  "total_dryer": 1,
  "store_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_name": "Downtown Laundry",
  "order_details": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "created_at": "2025-01-27T15:30:00Z",
      "updated_at": "2025-01-27T15:30:00Z",
      "status": "NEW",
      "machine_id": "550e8400-e29b-41d4-a716-446655440001",
      "order_id": "550e8400-e29b-41d4-a716-446655440003",
      "add_ons": [
        {
          "type": "DETERGENT",
          "price": 5000.00,
          "is_default": false,
          "quantity": 1
        },
        {
          "type": "SOFTENER",
          "price": 3000.00,
          "is_default": false,
          "quantity": 1
        }
      ],
      "price": 15.00,
      "machine_name": "Washer #1",
      "machine_type": "WASHER"
    }
  ]
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `404 Not Found` - Store or machine not found
- `409 Conflict` - Machine not available

### Get Order

Retrieves an order by ID with all details.

**Endpoint:** `GET /api/v1/order/{order_id}`

**Path Parameters:**
- `order_id` (UUID) - The order ID

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:30:00Z",
  "status": "IN_PROGRESS",
  "total_amount": 25.50,
  "total_washer": 1,
  "total_dryer": 1,
  "store_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_name": "Downtown Laundry",
  "order_details": [...]
}
```

**Error Responses:**
- `404 Not Found` - Order not found

### Update Order Status

Updates the status of an order.

**Endpoint:** `PUT /api/v1/order/{order_id}/status`

**Path Parameters:**
- `order_id` (UUID) - The order ID

**Request Body:**
```json
{
  "status": "IN_PROGRESS"
}
```

**Valid Status Values:**
- `NEW`
- `CANCELLED`
- `WAITING_FOR_PAYMENT`
- `PAYMENT_FAILED`
- `PAYMENT_SUCCESS`
- `IN_PROGRESS`
- `FINISHED`

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:35:00Z",
  "status": "IN_PROGRESS",
  "total_amount": 25.50,
  "total_washer": 1,
  "total_dryer": 1,
  "store_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_name": "Downtown Laundry",
  "order_details": []
}
```

**Error Responses:**
- `400 Bad Request` - Invalid status transition
- `404 Not Found` - Order not found

### Cancel Order

Cancels an order and frees up associated machines.

**Endpoint:** `POST /api/v1/order/{order_id}/cancel`

**Path Parameters:**
- `order_id` (UUID) - The order ID

**Request Body (Optional):**
```json
{
  "reason": "Customer requested cancellation",
  "refund_requested": true
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:40:00Z",
  "status": "CANCELLED",
  "total_amount": 25.50,
  "total_washer": 1,
  "total_dryer": 1,
  "store_id": "550e8400-e29b-41d4-a716-446655440000",
  "store_name": "Downtown Laundry",
  "order_details": []
}
```

**Error Responses:**
- `400 Bad Request` - Order cannot be cancelled
- `404 Not Found` - Order not found

### List Orders

Lists orders with pagination and filtering.

**Endpoint:** `GET /api/v1/order/`

**Query Parameters:**
- `page` (integer, optional) - Page number (default: 1)
- `per_page` (integer, optional) - Items per page (default: 20, max: 100)
- `store_id` (UUID, optional) - Filter by store ID
- `status` (string, optional) - Filter by order status
- `start_date` (datetime, optional) - Filter from date
- `end_date` (datetime, optional) - Filter to date

**Response (200 OK):**
```json
{
  "orders": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "created_at": "2025-01-27T15:30:00Z",
      "updated_at": "2025-01-27T15:30:00Z",
      "status": "IN_PROGRESS",
      "total_amount": 25.50,
      "total_washer": 1,
      "total_dryer": 1,
      "store_id": "550e8400-e29b-41d4-a716-446655440000",
      "store_name": "Downtown Laundry",
      "order_details": []
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

### Get Store Orders

Gets orders for a specific store.

**Endpoint:** `GET /api/v1/order/stores/{store_id}/orders`

**Path Parameters:**
- `store_id` (UUID) - The store ID

**Query Parameters:**
- `page` (integer, optional) - Page number (default: 1)
- `per_page` (integer, optional) - Items per page (default: 20, max: 100)
- `status` (string, optional) - Filter by order status
- `start_date` (datetime, optional) - Filter from date
- `end_date` (datetime, optional) - Filter to date

**Response (200 OK):**
```json
{
  "orders": [...],
  "total": 5,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

## Order Detail Management Endpoints

### Add Order Detail

Adds a machine booking to an existing order.

**Endpoint:** `POST /api/v1/order/{order_id}/details`

**Path Parameters:**
- `order_id` (UUID) - The order ID

**Request Body:**
```json
{
  "machine_id": "550e8400-e29b-41d4-a716-446655440005",
  "add_ons": [
    {
      "type": "DETERGENT",
      "price": 5000.00,
      "is_default": false,
      "quantity": 1
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440006",
  "created_at": "2025-01-27T15:30:00Z",
  "updated_at": "2025-01-27T15:30:00Z",
  "status": "NEW",
  "machine_id": "550e8400-e29b-41d4-a716-446655440005",
  "order_id": "550e8400-e29b-41d4-a716-446655440003",
  "add_ons": [
    {
      "type": "DETERGENT",
      "price": 5000.00,
      "is_default": false,
      "quantity": 1
    }
  ],
  "price": 12.00,
  "machine_name": "Dryer #1",
  "machine_type": "DRYER"
}
```

### Get Order Details

Gets all order details for an order.

**Endpoint:** `GET /api/v1/order/{order_id}/details`

**Path Parameters:**
- `order_id` (UUID) - The order ID

**Response (200 OK):**
```json
{
  "order_details": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "created_at": "2025-01-27T15:30:00Z",
      "updated_at": "2025-01-27T15:30:00Z",
      "status": "IN_PROGRESS",
      "machine_id": "550e8400-e29b-41d4-a716-446655440001",
      "order_id": "550e8400-e29b-41d4-a716-446655440003",
      "add_ons": [
        {
          "type": "DETERGENT",
          "price": 5000.00,
          "is_default": false,
          "quantity": 1
        }
      ],
      "price": 15.00,
      "machine_name": "Washer #1",
      "machine_type": "WASHER"
    }
  ],
  "total": 1
}
```

### Update Order Detail Status

Updates the status of an order detail.

**Endpoint:** `PUT /api/v1/order/{order_id}/details/{detail_id}/status`

**Path Parameters:**
- `order_id` (UUID) - The order ID
- `detail_id` (UUID) - The order detail ID

**Request Body:**
```json
{
  "status": "FINISHED"
}
```

**Valid Status Values:**
- `NEW`
- `IN_PROGRESS`
- `FINISHED`
- `CANCELLED`

### Cancel Order Detail

Cancels an order detail and frees up the machine.

**Endpoint:** `POST /api/v1/order/{order_id}/details/{detail_id}/cancel`

**Path Parameters:**
- `order_id` (UUID) - The order ID
- `detail_id` (UUID) - The order detail ID

## Machine Availability Endpoints

### Get Machine Availability

Gets the availability status of a machine.

**Endpoint:** `GET /api/v1/order/machines/{machine_id}/availability`

**Path Parameters:**
- `machine_id` (UUID) - The machine ID

**Response (200 OK):**
```json
{
  "machine_id": "550e8400-e29b-41d4-a716-446655440001",
  "machine_name": "Washer #1",
  "machine_type": "WASHER",
  "is_available": true,
  "current_status": "IDLE",
  "base_price": 15.00
}
```

**Response (409 Conflict) - Machine not available:**
```json
{
  "detail": "Machine is currently booked"
}
```

## Statistics Endpoints

### Get Store Order Statistics

Gets comprehensive statistics for a store's orders.

**Endpoint:** `GET /api/v1/order/stores/{store_id}/statistics`

**Path Parameters:**
- `store_id` (UUID) - The store ID

**Query Parameters:**
- `start_date` (datetime, optional) - Filter from date
- `end_date` (datetime, optional) - Filter to date

**Response (200 OK):**
```json
{
  "total_orders": 150,
  "total_revenue": 3750.00,
  "orders_by_status": {
    "NEW": 5,
    "WAITING_FOR_PAYMENT": 10,
    "IN_PROGRESS": 8,
    "FINISHED": 120,
    "CANCELLED": 7
  },
  "orders_by_store": {
    "Downtown Laundry": 150
  },
  "average_order_value": 25.00,
  "total_washers_booked": 120,
  "total_dryers_booked": 100
}
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
- `409 Conflict` - Resource conflict (e.g., machine not available)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Validation Errors

When validation fails, the API returns detailed error information:

```json
{
  "detail": [
    {
      "loc": ["body", "machine_selections", 0, "machine_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Order Creation**: 10 requests per minute per user
- **Status Updates**: 30 requests per minute per user
- **General Endpoints**: 100 requests per minute per user

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Examples

### Complete Order Flow

1. **Create Order:**
```bash
curl -X POST "https://api.lms.com/api/v1/order/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "550e8400-e29b-41d4-a716-446655440000",
    "machine_selections": [
      {
        "machine_id": "550e8400-e29b-41d4-a716-446655440001",
        "add_ons": {"detergent": "extra"},
        "price": 15.00
      }
    ]
  }'
```

2. **Create Payment:**
```bash
curl -X POST "https://api.lms.com/api/v1/payment/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "550e8400-e29b-41d4-a716-446655440003",
    "payment_method": "QR",
    "amount": 15.00,
    "currency": "USD"
  }'
```

3. **Update Payment Status (via callback):**
```bash
curl -X POST "https://api.lms.com/api/v1/payment/callback/PAY-ABC123?status=SUCCESS&transaction_id=txn_123456"
```

4. **Complete Order:**
```bash
curl -X PUT "https://api.lms.com/api/v1/order/550e8400-e29b-41d4-a716-446655440003/status" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "FINISHED"}'
```

5. **Cancel Order (if needed):**
```bash
curl -X POST "https://api.lms.com/api/v1/order/550e8400-e29b-41d4-a716-446655440003/cancel" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Customer requested cancellation",
    "refund_requested": true
  }'
```

## SDK Examples

### Python

```python
import requests

# Create order
response = requests.post(
    "https://api.lms.com/api/v1/order/",
    headers={"Authorization": "Bearer <token>"},
    json={
        "store_id": "550e8400-e29b-41d4-a716-446655440000",
        "machine_selections": [
            {
                "machine_id": "550e8400-e29b-41d4-a716-446655440001",
                "add_ons": [
                    {
                        "type": "DETERGENT",
                        "price": 5000.00,
                        "is_default": false,
                        "quantity": 1
                    }
                ]
            }
        ]
    }
)

order = response.json()
print(f"Order created: {order['id']}")
```

### JavaScript

```javascript
// Create order
const response = await fetch('https://api.lms.com/api/v1/order/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    store_id: '550e8400-e29b-41d4-a716-446655440000',
    machine_selections: [
      {
        machine_id: '550e8400-e29b-41d4-a716-446655440001',
        add_ons: [
          {
            type: 'DETERGENT',
            price: 5000.00,
            is_default: false,
            quantity: 1
          }
        ]
      }
    ]
  })
});

const order = await response.json();
console.log(`Order created: ${order.id}`);
```
