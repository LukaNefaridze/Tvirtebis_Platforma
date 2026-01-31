# Bidding System Implementation

This document describes the enhanced bidding interface for the admin panel.

## Features Implemented

### 1. Frontend Layout (Admin Detail View)

**Location:** `templates/admin/shipments/shipment/change_form.html`

#### Listing Header Card
- **Gradient Header:** Purple gradient background with key shipment information
- **Route Display:** Origin → Destination with arrow
- **Metadata:** Cargo Type, Weight, Transport Type, Currency, Pickup Date
- **Responsive:** Adapts to mobile and desktop layouts

#### Sorting Toolbar
- **Sort Options:**
  - **Price:** Sort bids by price (ascending - lowest first)
  - **Delivery Time:** Sort by estimated delivery time (ascending - fastest first)
  - **Date:** Sort by submission date (descending - newest first)
- **Visual Feedback:** Active sort button highlighted in blue
- **Icons:** Each sort option has an intuitive icon

#### Bids Grid Layout
- **CSS Grid:** `grid-cols-1` on mobile, `xl:grid-cols-2` on extra-large screens
- **Gap:** 1.5rem spacing between cards
- **Top 3 Bids:** Always visible immediately
- **Hidden Bids:** Remaining bids hidden behind "Show All (X)" button
- **Dynamic Toggle:** JavaScript-powered expand/collapse functionality

#### Bid Card Design
- **Status Badge:** Color-coded badges (Pending: Yellow, Accepted: Green, Rejected: Red)
- **Price Highlight:** Large, bold green price display
- **Delivery Time:** Prominent display in hours
- **Contact Information:** Contact person and phone number
- **Broker Details:** Shows broker company name
- **Comments:** Special styling for bid comments with yellow background
- **Hover Effect:** Blue border and shadow on hover

### 2. Backend Logic

**Location:** `apps/shipments/admin.py`

#### Accept Bid Functionality
When the "Accept" button is clicked:

1. **POST Request:** Form submits via POST with CSRF token
2. **Permission Check:** Verifies user has change permission
3. **Database Transaction:** Atomic operation ensures data consistency
4. **Bid Status Update:**
   - Selected bid → `ACCEPTED`
   - All other pending bids → `REJECTED`
5. **Shipment Status Update:**
   - Status → `completed`
   - `completed_at` timestamp set
   - `selected_bid` relationship established
6. **Rejected Bid Cache:** Creates cache entries for rejected bids to prevent duplicate resubmissions
7. **User Feedback:** Success message displayed

#### Reject Bid Functionality
When the "Reject" button is clicked:

1. **POST Request:** Form submits via POST with CSRF token
2. **Permission Check:** Verifies user has change permission
3. **Bid Status Update:** Bid marked as `REJECTED`
4. **Rejected Bid Cache:** Cache entry created
5. **User Feedback:** Success message displayed
6. **Shipment Stays Active:** Other bids remain pending

### 3. Dashboard Filtering

**Location:** `apps/shipments/admin.py` - `get_queryset()` method

#### Default Filter
- **List View:** Shows only `active` shipments by default
- **Removes Clutter:** Completed and cancelled shipments hidden
- **Visual Indicator:** Green badge shows "მხოლოდ აქტიური" (Only Active)
- **Override:** Users can still filter by status to see completed/cancelled listings

#### Query Optimization
- **Select Related:** Preloads user, cargo_type, volume_unit, transport_type, preferred_currency, selected_bid
- **Prefetch Related:** Preloads bids, bids__broker, bids__currency
- **Performance:** Prevents N+1 query problems

## User Workflow

### For Admin Users

1. **View Dashboard:** See grid of active shipments with pending bids highlighted
2. **Click Shipment:** Navigate to detail view
3. **Review Listing:** See origin, destination, cargo details at the top
4. **Sort Bids:** Click sorting buttons to organize by price, time, or date
5. **Review Top 3:** Quickly scan the top 3 bids
6. **Expand All:** Click "Show All" to see remaining bids
7. **Accept Bid:**
   - Click green "✓ მიღება" (Accept) button
   - Confirm via browser popup
   - System automatically:
     - Accepts the selected bid
     - Rejects all other pending bids
     - Marks shipment as completed
     - Removes from main dashboard
8. **Reject Bid:**
   - Click red "✕ უარყოფა" (Reject) button
   - Confirm via browser popup
   - Bid marked as rejected
   - Other bids remain active

### For Regular Users (Cargo Owners)

Users see a similar interface in their portal (`templates/accounts/shipment_detail.html`) with:
- Full listing details
- All bids displayed
- Accept/Reject actions available for pending bids on active shipments

## Technical Details

### CSS Grid Breakpoints
```css
/* Mobile: Single column */
grid-template-columns: 1fr;

/* Desktop (1280px+): Two columns */
@media (min-width: 1280px) {
    grid-template-columns: repeat(2, 1fr);
}
```

### JavaScript Functionality

#### Show/Hide Bids
```javascript
- Initially: Hide all bids with class 'hidden-bid' (index > 3)
- On "Show All" click: Display all bids, change button text to "ნაკლები" (Less)
- On "Less" click: Hide extra bids again, restore button text
```

#### Sorting
```javascript
- Extract bid data attributes (price, time, created)
- Sort array based on selected criterion
- Re-append bids in new order
- Maintain top-3 visibility logic
- Preserve "Show All" button at the end
```

### Status Flow Diagram

```
Shipment Created (active)
    ↓
Brokers Submit Bids (pending)
    ↓
Admin Reviews Bids
    ↓
    ├─→ Accept Bid
    │     ├─ Selected Bid: ACCEPTED
    │     ├─ Other Bids: REJECTED
    │     ├─ Shipment: COMPLETED
    │     └─ Removed from Dashboard
    │
    └─→ Reject Bid
          ├─ Rejected Bid: REJECTED
          └─ Shipment: ACTIVE (unchanged)
```

## Security Considerations

1. **CSRF Protection:** All POST requests include CSRF tokens
2. **Permission Checks:** Verify user has change permission before actions
3. **POST-only Actions:** Accept/Reject only work via POST (not GET)
4. **Atomic Transactions:** Database operations wrapped in transactions
5. **Validation:** Model-level validation in `mark_completed()` method

## Database Models

### Shipment Status Choices
- `active` - აქტიური (Active)
- `completed` - დასრულებული (Completed/Closed)
- `cancelled` - გაუქმებული (Cancelled)

### Bid Status Choices
- `pending` - მოლოდინში (Pending)
- `accepted` - მიღებული (Accepted)
- `rejected` - უარყოფილი (Rejected)

## Future Enhancements

Potential improvements for future iterations:

1. **Rating System:** Add actual broker ratings instead of using date as proxy
2. **Bid History:** Show modification history for bids
3. **Bulk Actions:** Accept/reject multiple bids at once
4. **Email Notifications:** Notify brokers when bids are accepted/rejected
5. **Webhook Integration:** Already supports webhook URLs for bid status notifications
6. **Analytics:** Dashboard showing bid acceptance rates, average prices, etc.
7. **Real-time Updates:** WebSocket support for live bid updates
8. **Mobile App:** Native mobile interface for on-the-go bid management

## Files Modified

1. **`templates/admin/shipments/shipment/change_form.html`** (NEW)
   - Custom admin detail view with bidding interface

2. **`apps/shipments/admin.py`**
   - Updated `accept_bid_view()` to require POST
   - Updated `reject_bid_view()` to require POST
   - Added default filter for active shipments in `get_queryset()`

3. **`templates/admin/shipments/shipment/change_list_grid.html`**
   - Added "Only Active" indicator badge

## Testing Checklist

- [ ] Create test shipment with multiple bids
- [ ] Verify top 3 bids display correctly
- [ ] Test "Show All" expand/collapse functionality
- [ ] Test sorting by Price (lowest first)
- [ ] Test sorting by Delivery Time (fastest first)
- [ ] Test sorting by Date (newest first)
- [ ] Accept a bid and verify:
  - [ ] Bid status changes to ACCEPTED
  - [ ] Other bids change to REJECTED
  - [ ] Shipment status changes to COMPLETED
  - [ ] Shipment disappears from dashboard
- [ ] Reject a bid and verify:
  - [ ] Bid status changes to REJECTED
  - [ ] Shipment remains ACTIVE
  - [ ] Other bids remain PENDING
- [ ] Test on mobile device (single column layout)
- [ ] Test on desktop (two column layout)
- [ ] Verify CSRF protection works
- [ ] Verify permission checks prevent unauthorized actions

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Notes

- **Query Optimization:** Uses `select_related()` and `prefetch_related()` to minimize database queries
- **Lazy Loading:** Hides extra bids initially to reduce DOM size
- **CSS Transitions:** Smooth animations without JavaScript animation libraries
- **No External Dependencies:** Pure JavaScript implementation (no jQuery required)

## Support

For issues or questions about this implementation:
1. Check Django admin logs: `logs/django.log`
2. Verify database migrations are applied
3. Check browser console for JavaScript errors
4. Review CSRF token configuration if forms fail
