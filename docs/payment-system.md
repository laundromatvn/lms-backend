# Payment System Documentation

## Overview

The Payment System is a comprehensive solution for handling payment transactions in the Laundry Management System (LMS). It provides complete payment lifecycle management from initialization to completion, including QR code generation, payment processing, and status tracking for customer UI integration.

## System Architecture

### Core Components

1. **Payment Model** - Main payment entity with status management
3. **VietQR Integration** - QR code generation and payment processing
4. **Order Integration** - Seamless integration with order system
5. **API Layer** - RESTful endpoints for payment management
6. **Business Logic** - Payment operations and validation

### Database Schema

#### Payments Table
- `id` - UUID primary key
- `created_at`, `updated_at` - Timestamps
- `status` - Payment status (NEW, WAITING_FOR_PAYMENT_DETAIL, WAITING_FOR_PURCHASE, SUCCESS, FAILED, CANCELLED)
- `details` - JSON field for storing QR code and payment details
- `store_id` - Foreign key to stores table
- `tenant_id` - Foreign key to tenants table
- `total_amount` - Payment amount
- `provider` - Payment provider (VIET_QR)
- `provider_transaction_id` - Transaction ID from payment provider


### Payment Details Structure

Payment details are stored as JSON with the following structure:

```json
{
  "qr_code": "00020101021238570010A000000727012700069704080108QRIBFTTA53037045802VN6304A1B2",
  "qr_image_url": "https://api.vietqr.io/v2/generate/...",
  "expired_at": "2025-01-27T16:00:00Z",
  "payment_instructions": "Scan QR code to complete payment",
  "transaction_id": "vietqr_txn_123456",
  "transaction_ref_id": "ref_789012"
}
```

**Fields:**
- `qr_code` - QR code string for payment
- `qr_image_url` - URL to QR code image
- `expired_at` - Payment expiration time
- `payment_instructions` - Instructions for customer
- `transaction_id` - VietQR transaction ID
- `transaction_ref_id` - VietQR transaction reference ID

## Payment Flow

### 1. Payment Initialization
```
Order Created → Payment Initialization → Status: NEW
```

1. **Order Creation**: Order created with status WAITING_FOR_PAYMENT
2. **Payment Initialization**: PaymentTransaction created with status NEW
3. **Validation**: Order, store, and tenant validation
4. **Amount Verification**: Payment amount matches order total

### 2. Payment Detail Generation
```
Status: NEW → WAITING_FOR_PAYMENT_DETAIL → WAITING_FOR_PURCHASE
```

1. **QR Generation**: VietQR API called to generate QR code
2. **Detail Storage**: QR code and details stored in JSON field
3. **Status Update**: Status updated to WAITING_FOR_PURCHASE
4. **Customer Display**: QR code displayed to customer

### 3. Payment Processing
```
Customer Scans QR → Payment Processing → Status Update
```

1. **QR Scanning**: Customer scans QR code with banking app
2. **Payment Processing**: VietQR processes payment
3. **Status Monitoring**: Customer UI polls for payment status
4. **Completion**: Payment marked as SUCCESS or FAILED

### 4. Order Integration
```
Payment Success → Order Status Update → Machine Start
```

1. **Payment Success**: PaymentTransaction status updated to SUCCESS
2. **Order Update**: Order status updated to PAYMENT_SUCCESS
3. **Machine Start**: Machines started for order processing
4. **Completion**: Order moves to IN_PROGRESS status

## API Endpoints

### Payment Management

#### Initialize Payment
```http
POST /api/v1/payments/initialize
Content-Type: application/json

{
  "order_id": "uuid",
  "store_id": "uuid",
  "tenant_id": "uuid",
  "total_amount": 25.50,
  "provider": "VIET_QR"
}
```

#### Get Payment
```http
GET /api/v1/payments/{payment_id}
```

#### Check Payment Detail Status
```http
GET /api/v1/payments/{payment_id}/details/status
```

#### Get Payment Details
```http
GET /api/v1/payments/{payment_id}/details
```



## Business Rules

### Payment Creation
- Only one active payment per order
- Payment amount must match order total exactly
- Store and tenant must exist and be active
- Order must be in WAITING_FOR_PAYMENT status

### Status Transitions
- **NEW** → WAITING_FOR_PAYMENT_DETAIL, CANCELLED
- **WAITING_FOR_PAYMENT_DETAIL** → WAITING_FOR_PURCHASE, FAILED, CANCELLED
- **WAITING_FOR_PURCHASE** → SUCCESS, FAILED, CANCELLED
- **SUCCESS** → (no transitions)
- **FAILED** → NEW (allow retry)
- **CANCELLED** → (no transitions)

### Payment Integration
- VietQR is the primary payment provider
- QR codes expire after 30 minutes by default
- Payment details are generated asynchronously
- Customer UI polls for status updates

### Order Integration
- Successful payment automatically updates order status
- Failed payment allows order to be retried
- Cancelled payment cancels the associated order

## Error Handling

### Validation Errors
- Invalid UUID formats
- Negative payment amounts
- Invalid status transitions
- Missing required fields
- Amount mismatch with order total

### Business Logic Errors
- Order not found or cannot be paid
- Store or tenant not found
- Duplicate payment transaction
- Payment provider failures

### Database Errors
- Constraint violations
- Transaction failures
- Connection issues

## Security Considerations

### Authentication
- All endpoints require proper authentication
- User context tracked for audit trails
- Role-based access control

### Data Validation
- Input sanitization and validation
- SQL injection prevention through ORM
- XSS protection in API responses

### Payment Security
- QR code expiration handling
- Payment amount validation
- Transaction ID verification

## Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Query optimization for status checking
- Connection pooling

### Caching
- Payment status caching
- QR code caching
- Store and tenant information caching

### Monitoring
- Payment success rates
- QR generation performance
- API response times

## Testing

### Unit Tests
- Model validation and business logic
- Status transition validation
- Error handling scenarios

### Integration Tests
- API endpoint testing
- VietQR integration testing
- Order integration testing

### Performance Tests
- Load testing for payment initialization
- Concurrent payment processing
- Database performance under load

## Deployment

### Database Migrations
- Payment table creation
- Index creation
- Enum type creation

### Configuration
- VietQR API settings
- Payment timeout configurations
- QR code expiration settings

### Monitoring
- Payment processing metrics
- Error rate monitoring
- Performance dashboards

## Troubleshooting

### Common Issues

#### Payment Initialization Fails
- Check order status and availability
- Verify store and tenant existence
- Validate payment amount

#### QR Code Generation Issues
- Verify VietQR API configuration
- Check network connectivity
- Validate API credentials

#### Payment Status Not Updating
- Check payment provider callbacks
- Verify status transition rules
- Review payment operation logs

### Debugging
- Enable detailed logging
- Check database transaction logs
- Monitor API request/response logs

## Future Enhancements

### Planned Features
- Multiple payment providers support
- Payment retry mechanisms
- Advanced payment analytics
- Real-time payment notifications
- Payment scheduling

### Scalability Improvements
- Microservices architecture
- Event-driven processing
- Distributed caching
- Load balancing

## Support

For technical support or questions about the Payment System:

1. Check the API documentation
2. Review error logs and monitoring
3. Contact the development team
4. Submit issues through the project repository
