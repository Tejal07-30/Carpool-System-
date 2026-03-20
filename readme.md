 # Carpool System (DVM Project)

A backend system designed to make daily commuting easier by connecting riders and drivers through shared routes.

# Project Status

Currently in development
Core features are implemented and being tested.
Deployment is *ongoing* and will be completed soon.

# What This Project Does

Instead of random ride matching, this system uses a structured route network:

* Locations are treated as nodes
* Paths between them are edges
* Trips follow a predefined route order

# Key Features

1. User System

* Authentication using Django AllAuth
* Google login support (OAuth)
* Custom user model

2. Route & Network System

* Nodes represent locations (e.g., Rajiv Chowk, Pitampura)
* Edges define connectivity between nodes
* Trips follow ordered routes using `TripRoute`

3. Carpool Flow

* Riders can create ride requests
* Drivers can view and respond with offers
* Riders can accept offers

4. Wallet System

* Each user has a wallet
* Fare is calculated based on route
* Automatic debit (rider) and credit (driver)

5. Trip Management

* Real-time trip updates
* Node-based movement tracking
* Trip status handling

---

# How It Works 

1. User logs in
2. Rider creates a request (pickup → drop)
3. System checks if route exists
4. Driver sends offer
5. Rider accepts offer
6. Payment is processed via wallet

---

# Tech Stack Used

* Backend: Django, Django REST Framework
* Database: PostgreSQL
* Authentication: Django AllAuth + Google OAuth
* API Testing: DRF Browsable API

---

# Main Modules

* `users` → Custom user model & authentication
* `network` → Nodes and edges (graph system)
* `trips` → Trips and route ordering
* `carpool` → Requests, offers, matching logic
* `wallet` → Transactions and balances
* `api` → All REST endpoints

---

# Testing

Testing is done using:

* Django Admin panel (for data setup)
* DRF API interface (for endpoints)
