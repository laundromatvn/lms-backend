# Order Management System Documentation

## Overview

The Order Management System is a comprehensive solution for handling laundry orders in the Laundry Management System (LMS). It provides complete order lifecycle management from creation to completion, including machine booking, payment processing, and status tracking.

## System Architecture

### Core Components

1. **Order Model** - Main order entity with status management
2. **OrderDetail Model** - Individual machine bookings within an order
3. **Payment Integration** - Seamless payment processing
4. **Machine Integration** - Automatic machine status updates
5. **API Layer** - RESTful endpoints for order management
6. **Business Logic** - Order operations and validation

### Database Schema

#### Orders Table
- `id` - UUID primary key
- `created_at`, `updated_at` - Timestamps
- `status` - Order status (NEW, CANCELLED, WAITING_FOR_PAYMENT, PAYMENT_FAILED, PAYMENT_SUCCESS, IN_PROGRESS, FINISHED)
- `total_amount` - Total order amount
- `total_washer` - Number of washers booked
- `total_dryer` - Number of dryers booked
- `store_id` - Foreign key to stores table

#### Order Details Table
- `id` - UUID primary key
- `order_id` - Foreign key to orders table
- `machine_id` - Foreign key to machines table
- `status` - Order detail status (NEW, IN_PROGRESS, FINISHED, CANCELLED)
- `add_ons` - JSON array of additional services with standardized structure (unlimited size)
- `price` - Individual machine price

### Add-ons Structure

Add-ons are stored as a JSON array with the following standardized structure:

```json
[
  {
    "type": "HOT_WATER" | "COLD_WATER" | "DETERGENT" | "SOFTENER" | "DRYING_DURATION_MINUTE",
    "price": 5000.00,
    "is_default": true | false,
    "quantity": 1
  }
]
```

**Fields:**
- `type` - The type of add-on service
- `price` - Price for this add-on (in smallest currency unit)
- `is_default` - Whether this add-on is included by default
- `quantity` - Quantity of this add-on

**Supported Add-on Types:**
- `HOT_WATER` - Hot water service
- `COLD_WATER` - Cold water service  
- `DETERGENT` - Detergent/cleaning agent
- `SOFTENER` - Fabric softener
- `DRYING_DURATION_MINUTE` - Extended drying time

### Price Calculation

Order prices are calculated automatically based on:

1. **Machine Base Price**: Each machine has a base price defined in the system
2. **Add-ons Price**: Sum of all selected add-ons (price × quantity)
3. **Total Order Price**: Sum of all machine prices (base + add-ons)

**Formula:**
```
Order Total = Σ(Machine Base Price + Σ(Add-on Price × Quantity))
```

**Example:**
- Machine base price: $15.00
- Add-ons: DETERGENT ($5.00 × 1) + SOFTENER ($3.00 × 1) = $8.00
- **Total**: $15.00 + $8.00 = $23.00

## Order Flow

### 1. Order Creation
```
User selects machines → Order Preview → Order Creation → Payment Processing
```

1. **Machine Selection**: User selects washer, dryer, or both
2. **Order Preview**: System shows order summary with pricing
3. **Order Creation**: Order created with status NEW
4. **Payment Processing**: Order moves to WAITING_FOR_PAYMENT status

### 2. Payment Flow
```
Payment Creation → Payment Processing → Status Update → Order Execution
```

1. **Payment Creation**: Payment record created for the order
2. **Payment Processing**: External payment provider processes payment
3. **Status Update**: Payment status updated via callback
4. **Order Execution**: Order status updated and machines started

### 3. Order Completion
```
Machine Operation → Order Completion → Status Update → Machine Release
```

1. **Machine Operation**: Machines run the laundry cycle
2. **Order Completion**: Order marked as FINISHED
3. **Status Update**: All order details marked as FINISHED
4. **Machine Release**: Machines returned to IDLE status

## API Endpoints

### Order Management

#### Create Order
```http
POST /api/v1/order/
Content-Type: application/json

{
  "store_id": "uuid",
  "machine_selections": [
    {
      "machine_id": "uuid",
      "add_ons": {"detergent": "extra"},
      "price": 15.00
    }
  ]
}
```

#### Get Order
```http
GET /api/v1/order/{order_id}
```

#### Update Order Status
```http
PUT /api/v1/order/{order_id}/status
Content-Type: application/json

{
  "status": "IN_PROGRESS"
}
```

#### Cancel Order
```http
POST /api/v1/order/{order_id}/cancel
```

#### Get Store Orders
```http
GET /api/v1/order/stores/{store_id}/orders?page=1&per_page=20
```

### Order Detail Management

#### Add Order Detail
```http
POST /api/v1/order/{order_id}/details
Content-Type: application/json

{
  "machine_id": "uuid",
  "add_ons": {"detergent": "extra"},
  "price": 15.00
}
```

#### Get Order Details
```http
GET /api/v1/order/{order_id}/details
```

#### Update Order Detail Status
```http
PUT /api/v1/order/{order_id}/details/{detail_id}/status
Content-Type: application/json

{
  "status": "IN_PROGRESS"
}
```

#### Cancel Order Detail
```http
POST /api/v1/order/{order_id}/details/{detail_id}/cancel
```

### Payment Integration

#### Create Payment
```http
POST /api/v1/payment/
Content-Type: application/json

{
  "order_id": "uuid",
  "payment_method": "QR",
  "amount": 25.50,
  "currency": "USD"
}
```

#### Update Payment Status
```http
PUT /api/v1/payment/{payment_id}/status
Content-Type: application/json

{
  "status": "SUCCESS",
  "transaction_id": "txn_123456",
  "payment_reference": "PAY-ABC123"
}
```

#### Payment Callback
```http
POST /api/v1/payment/callback/{payment_reference}?status=SUCCESS&transaction_id=txn_123456
```

## Business Rules

### Order Creation
- Orders can only be created for active stores
- Machines must be in IDLE status to be booked
- At least one machine selection is required
- Order amount is calculated automatically from machine base price plus add-ons
- Client should not provide price - it's calculated server-side

### Status Transitions
- **NEW** → WAITING_FOR_PAYMENT, CANCELLED
- **WAITING_FOR_PAYMENT** → PAYMENT_SUCCESS, PAYMENT_FAILED, CANCELLED
- **PAYMENT_FAILED** → WAITING_FOR_PAYMENT, CANCELLED
- **PAYMENT_SUCCESS** → IN_PROGRESS
- **IN_PROGRESS** → FINISHED, CANCELLED
- **CANCELLED** → (no transitions)
- **FINISHED** → (no transitions)

### Payment Integration
- Only one active payment per order
- Payment amount must match order total
- Successful payment automatically starts machines
- Failed payment allows retry

### Machine Management
- Only IDLE machines can be booked
- Machine status updated automatically with order status
- Cancelled orders free up machines immediately

## Error Handling

### Validation Errors
- Invalid UUID formats
- Negative amounts or counts
- Invalid status transitions
- Missing required fields

### Business Logic Errors
- Store not found or inactive
- Machine not available
- Order cannot be modified
- Payment validation failures

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

### Rate Limiting
- Order creation rate limiting
- Payment processing limits
- API endpoint throttling

## Performance Considerations

### Database Optimization
- Proper indexing on frequently queried fields
- Query optimization for large datasets
- Connection pooling

### Caching
- Order status caching
- Machine availability caching
- Store information caching

### Monitoring
- Order processing metrics
- Payment success rates
- Machine utilization tracking

## Testing

### Unit Tests
- Model validation and business logic
- Status transition validation
- Error handling scenarios

### Integration Tests
- API endpoint testing
- Payment flow testing
- Machine integration testing

### Performance Tests
- Load testing for order creation
- Concurrent booking scenarios
- Database performance under load

## Deployment

### Database Migrations
- Order table creation
- Order detail table creation
- Payment table updates
- Index creation

### Configuration
- Payment provider settings
- Order timeout configurations
- Machine status update intervals

### Monitoring
- Order processing metrics
- Error rate monitoring
- Performance dashboards

## Troubleshooting

### Common Issues

#### Order Creation Fails
- Check store status and availability
- Verify machine availability
- Validate input data format

#### Payment Processing Issues
- Verify payment provider configuration
- Check callback URL accessibility
- Validate payment reference format

#### Machine Status Not Updating
- Check machine availability
- Verify order status transitions
- Review machine operation logs

### Debugging
- Enable detailed logging
- Check database transaction logs
- Monitor API request/response logs

## Future Enhancements

### Planned Features
- Order scheduling and reservations
- Bulk order processing
- Advanced reporting and analytics
- Mobile app integration
- Real-time notifications

### Scalability Improvements
- Microservices architecture
- Event-driven processing
- Distributed caching
- Load balancing

## Support

For technical support or questions about the Order Management System:

1. Check the API documentation
2. Review error logs and monitoring
3. Contact the development team
4. Submit issues through the project repository
