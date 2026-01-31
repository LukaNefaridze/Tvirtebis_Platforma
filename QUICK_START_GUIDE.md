# Quick Start Guide - Bidding System

## 🚀 Getting Started

This guide will help you quickly understand and use the new bidding system.

## 📍 Where to Find Things

### For Admins

**Shipment Dashboard (Main View)**
- **URL:** `/admin/shipments/shipment/`
- **Shows:** Active shipments with bids
- **Actions:** Accept/Reject bids
- **Layout:** Card grid (2 columns on desktop)

**Bids History Page**
- **URL:** `/admin/bids/bid/`
- **Shows:** All bids in table format
- **Actions:** View details, filter, search
- **Layout:** Table with modal details

**Navigation:**
```
Admin Panel
├─ 📦 განაცხადები (Shipments) → Dashboard
└─ 🔨 ბიდები (Bids) → History Page
```

## 🎯 Common Tasks

### Task 1: Review and Accept a Bid

```
1. Go to Shipments (განაცხადები)
   └─ You'll see a grid of active shipments

2. Click on any shipment card
   └─ Opens detail view

3. Review the listing header
   ✓ Origin → Destination
   ✓ Cargo type and weight
   ✓ Transport type
   ✓ Preferred currency
   ✓ Pickup date

4. Review bids
   ✓ Top 3 bids shown by default
   ✓ Click "Show All" to see more

5. Sort bids (optional)
   ✓ Click "Price" for cheapest first
   ✓ Click "Time" for fastest first
   ✓ Click "Date" for newest first

6. Accept a bid
   ✓ Click green "✓ მიღება" button
   ✓ Confirm in popup
   ✓ Done! Shipment is now completed

Result:
✅ Selected bid → ACCEPTED
✅ Other bids → REJECTED
✅ Shipment → COMPLETED
✅ Removed from dashboard
```

### Task 2: Reject a Bid

```
1. Open shipment detail (same as above)

2. Find the bid you want to reject

3. Click red "✕ უარყოფა" button
   └─ Confirm in popup

Result:
✅ Bid → REJECTED
✅ Shipment stays ACTIVE
✅ Other bids stay PENDING
```

### Task 3: View Bid History

```
1. Click "ბიდები" (Bids) in menu

2. You'll see a table with all bids

3. Use filters (optional)
   ✓ Status: Pending/Accepted/Rejected
   ✓ Date range
   ✓ Currency
   ✓ Broker

4. Click "👁️ ნახვა" on any bid
   └─ Modal opens with full details
   └─ Shows contact info and comments
   └─ Close with X, ESC, or click outside

5. Click Shipment ID to see full context
```

### Task 4: Search for Specific Bids

```
1. Go to Bids page (ბიდები)

2. Use the search box

3. Search by:
   ✓ Company name
   ✓ Broker name
   ✓ Contact person
   ✓ Shipment location

4. Results filter instantly
```

## 🎨 Visual Guide

### Shipment Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📦 განაცხადები                          [+ ახალი განაცხადი] │
│                                                               │
│  25 განაცხადი [მხოლოდ აქტიური]                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ [ID] [აქტიური]      │  │ [ID] [აქტიური]      │         │
│  │                      │  │                      │         │
│  │ 📍 Tbilisi → Batumi │  │ 📍 Batumi → Kutaisi │         │
│  │                      │  │                      │         │
│  │ 📦 15 ტონა • სურსათი │  │ 📦 8 ტონა • ავეჯი   │         │
│  │ 🚚 სატვირთო          │  │ 🚚 ფურგონი          │         │
│  │ 📅 01.02.2026        │  │ 📅 02.02.2026        │         │
│  │                      │  │                      │         │
│  │ 📋 5 ბიდი (3 ახალი)  │  │ 📋 2 ბიდი           │         │
│  │                      │  │                      │         │
│  │      [ნახვა]         │  │      [ნახვა]         │         │
│  └──────────────────────┘  └──────────────────────┘         │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ ... more cards ...   │  │ ... more cards ...   │         │
│  └──────────────────────┘  └──────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Shipment Detail View

```
┌─────────────────────────────────────────────────────────────┐
│  ← უკან განაცხადებზე                                        │
├─────────────────────────────────────────────────────────────┤
│  ╔═══════════════════════════════════════════════════════╗  │
│  ║  Tbilisi → Batumi                                     ║  │
│  ║  📦 სურსათი  ⚖️ 15 ტონა  🚚 სატვირთო  💰 GEL  📅 01.02 ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
│                                                               │
│  შეთავაზებები (5)                                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Sort By: [💰 Price] [⏰ Time] [📅 Date]              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Company ABC        │  │ Company XYZ        │            │
│  │ Broker: FastShip   │  │ Broker: QuickMove  │            │
│  │                    │  │                    │            │
│  │ 1,200 ₾      24სთ  │  │ 1,350 ₾      18სთ  │            │
│  │                    │  │                    │            │
│  │ Contact: Giorgi    │  │ Contact: Tamari    │            │
│  │ Phone: 555 123 456 │  │ Phone: 555 789 012 │            │
│  │                    │  │                    │            │
│  │ 💬 Comment here... │  │                    │            │
│  │                    │  │                    │            │
│  │ [✓ მიღება] [✕ უარყოფა] │ [✓ მიღება] [✕ უარყოფა]│            │
│  └────────────────────┘  └────────────────────┘            │
│                                                               │
│  ┌────────────────────┐                                     │
│  │ Company 123        │                                     │
│  │ ... 3rd bid ...    │                                     │
│  └────────────────────┘                                     │
│                                                               │
│         [Show All (2 more)]                                  │
└─────────────────────────────────────────────────────────────┘
```

### Bids History Page

```
┌─────────────────────────────────────────────────────────────┐
│  🔨 ბიდები                                                   │
│                                                               │
│  Filters: [Status ▼] [Date ▼] [Currency ▼] [Broker ▼]      │
│  Search: [_________________________________] 🔍              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Bid ID   | Shipment ID      | Company | Price  | Time | ... │
│  --------- ------------------ --------- -------- ------ -----│
│  a1b2c3d4 | x9y8z7w6         | ABC Inc | 1,200₾ | 24სთ | 👁️ │
│            Tbilisi→Batumi                                [ნახვა] │
│  --------- ------------------ --------- -------- ------ -----│
│  e5f6g7h8 | x9y8z7w6         | XYZ Ltd | 1,350₾ | 18სთ | 👁️ │
│            Tbilisi→Batumi                                [ნახვა] │
│  --------- ------------------ --------- -------- ------ -----│
│  ... more rows ...                                           │
└─────────────────────────────────────────────────────────────┘
```

### Modal Detail View

```
Click "👁️ ნახვა" button:

┌─────────────────────────────────────────────────────────────┐
│                                                               │
│    ┌───────────────────────────────────────────────┐        │
│    │ ბიდის დეტალები                           [✕] │        │
│    ├───────────────────────────────────────────────┤        │
│    │                                               │        │
│    │ COMPANY & BROKER                              │        │
│    │ Company: ABC Transport                        │        │
│    │ Broker: FastShip LLC                          │        │
│    │                                               │        │
│    │ PRICE & DELIVERY                              │        │
│    │ Price: 1,200 ₾ ◄── Large green text         │        │
│    │ Delivery: 24 hours                            │        │
│    │                                               │        │
│    │ CONTACT INFORMATION                           │        │
│    │ Person: Giorgi Beridze                        │        │
│    │ Phone: +995 555 123 456                       │        │
│    │                                               │        │
│    │ COMMENT                                       │        │
│    │ 💬 We can provide extra insurance...          │        │
│    │                                               │        │
│    │ STATUS & DATE                                 │        │
│    │ Status: [მოლოდინში] ◄── Yellow badge         │        │
│    │ Created: 31.01.2026 14:30                     │        │
│    │                                               │        │
│    ├───────────────────────────────────────────────┤        │
│    │                            [Close Button]     │        │
│    └───────────────────────────────────────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Color Guide

### Status Colors

**Pending (მოლოდინში):**
- 🟡 Yellow badge
- Means: Waiting for decision

**Accepted (მიღებული):**
- 🟢 Green badge
- Means: Bid was accepted

**Rejected (უარყოფილი):**
- 🔴 Red badge
- Means: Bid was rejected

### UI Element Colors

- **Prices:** 🟢 Green (positive, money)
- **Actions:** 🔵 Blue (interactive)
- **Accept Button:** 🟢 Green (positive action)
- **Reject Button:** 🔴 Red (negative action)
- **Headers:** 🟣 Purple gradient (decorative)

## ⌨️ Keyboard Shortcuts

**On Bids History Page:**
- `TAB` - Navigate between elements
- `ENTER` - Open modal on focused "View" button
- `ESC` - Close modal

**Browser Shortcuts:**
- `Ctrl+F` / `Cmd+F` - Find in page
- `F5` - Refresh page
- `Ctrl+R` / `Cmd+R` - Reload

## 📱 Mobile Usage

### On Phone/Tablet:

**Shipment Dashboard:**
- Cards stack vertically (single column)
- All information visible
- Touch-friendly buttons

**Bid Details:**
- Swipe to scroll through bids
- Tap to expand/collapse
- Large touch targets (min 44px)

**Bids History:**
- Table scrolls horizontally
- Tap "View" to open modal
- Modal fills screen

## ❓ Common Questions

### Q: Where did my shipment go after accepting a bid?
**A:** Completed shipments are hidden from the main dashboard (which shows only ACTIVE). Use the status filter to see completed shipments.

### Q: Can I undo accepting a bid?
**A:** No, accept actions are final. The shipment status changes to COMPLETED.

### Q: How do I see all bids on a shipment?
**A:** Click "Show All (X)" button in the shipment detail view, or go to Bids History page and filter by shipment ID.

### Q: What happens to other bids when I accept one?
**A:** All other pending bids are automatically rejected.

### Q: Can I edit a bid?
**A:** No, bids are read-only for audit purposes. Only status can change.

### Q: How do I contact a bidder?
**A:** Contact information (phone and person name) is shown in the bid card and modal details.

## 🐛 Troubleshooting

### Modal won't open
1. Check if JavaScript is enabled
2. Clear browser cache (Ctrl+Shift+R)
3. Try different browser

### Buttons not working
1. Check internet connection
2. Refresh the page
3. Check browser console for errors

### Can't see any shipments
1. Check status filter (default: Active only)
2. Verify you have shipments created
3. Check if you're using correct user account

### Bids not sorted correctly
1. Click sort button again
2. Refresh the page
3. Clear browser cache

## 📞 Getting Help

**Check Documentation:**
1. `COMPLETE_IMPLEMENTATION.md` - Full overview
2. `BIDDING_SYSTEM.md` - Shipment dashboard details
3. `BIDS_HISTORY_PAGE.md` - Bids page details

**Common Locations:**
- Admin Panel: `/admin/`
- Shipments: `/admin/shipments/shipment/`
- Bids: `/admin/bids/bid/`

**Need More Help?**
- Check server logs: `logs/django.log`
- Check browser console: Press F12
- Review error messages carefully

## ✅ Quick Checklist

**First Time Setup:**
- [ ] Server is running
- [ ] Database migrations applied
- [ ] Admin account created
- [ ] Logged into admin panel
- [ ] Can see shipments dashboard
- [ ] Can see bids history page

**Daily Usage:**
- [ ] Check dashboard for new bids
- [ ] Review and accept/reject bids
- [ ] Use filters to find specific bids
- [ ] Check bid history for trends

**Before Accepting Bid:**
- [ ] Reviewed all available bids
- [ ] Compared prices
- [ ] Checked delivery times
- [ ] Verified contact information
- [ ] Read any comments
- [ ] Confirmed decision

## 🎉 You're Ready!

The bidding system is now at your fingertips. Start reviewing and accepting bids with confidence!

### Quick Links:
- 📦 [Shipments Dashboard](/admin/shipments/shipment/)
- 🔨 [Bids History](/admin/bids/bid/)
- 👤 [Admin Home](/admin/)

---

**Happy Bidding!** 🚀
