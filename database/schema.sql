-- Database schema for SQL Agent
-- Tables: customers, offers, subscriptions

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    registration_date DATE NOT NULL,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'USA',
    postal_code TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Offers table
CREATE TABLE IF NOT EXISTS offers (
    offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    duration_months INTEGER NOT NULL,
    available_cities TEXT, -- Comma-separated list of cities where offer is available
    available_states TEXT, -- Comma-separated list of states where offer is available
    available_countries TEXT DEFAULT 'USA', -- Comma-separated list of countries
    is_location_specific BOOLEAN DEFAULT 0, -- Whether offer is location-restricted
    max_distance_km INTEGER, -- Maximum distance from offer center (for location-based offers)
    offer_center_latitude DECIMAL(10, 8), -- Center point for distance-based offers
    offer_center_longitude DECIMAL(11, 8), -- Center point for distance-based offers
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status TEXT CHECK(status IN ('active', 'expired', 'cancelled')) DEFAULT 'active',
    payment_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_registration_date ON customers(registration_date);
CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
CREATE INDEX IF NOT EXISTS idx_customers_state ON customers(state);
CREATE INDEX IF NOT EXISTS idx_customers_location ON customers(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_offers_location_specific ON offers(is_location_specific);
CREATE INDEX IF NOT EXISTS idx_offers_cities ON offers(available_cities);
CREATE INDEX IF NOT EXISTS idx_offers_states ON offers(available_states);
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_offer_id ON subscriptions(offer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_start_date ON subscriptions(start_date);

-- Views for easier querying

-- View for customers with their available offers based on location
CREATE VIEW IF NOT EXISTS customer_available_offers AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.city,
    c.state,
    c.country,
    o.offer_id,
    o.offer_name,
    o.description,
    o.price,
    o.duration_months,
    o.is_location_specific,
    CASE 
        WHEN o.is_location_specific = 0 THEN 'Available'
        WHEN o.available_cities IS NOT NULL AND c.city IN (
            SELECT TRIM(value) FROM (
                WITH RECURSIVE split(str, rest) AS (
                    SELECT '', o.available_cities || ','
                    UNION ALL
                    SELECT 
                        SUBSTR(rest, 1, INSTR(rest, ',') - 1),
                        SUBSTR(rest, INSTR(rest, ',') + 1)
                    FROM split 
                    WHERE rest != ''
                )
                SELECT str AS value FROM split WHERE str != ''
            )
        ) THEN 'Available'
        WHEN o.available_states IS NOT NULL AND c.state IN (
            SELECT TRIM(value) FROM (
                WITH RECURSIVE split(str, rest) AS (
                    SELECT '', o.available_states || ','
                    UNION ALL
                    SELECT 
                        SUBSTR(rest, 1, INSTR(rest, ',') - 1),
                        SUBSTR(rest, INSTR(rest, ',') + 1)
                    FROM split 
                    WHERE rest != ''
                )
                SELECT str AS value FROM split WHERE str != ''
            )
        ) THEN 'Available'
        WHEN o.max_distance_km IS NOT NULL AND (
            6371 * acos(
                cos(radians(c.latitude)) * cos(radians(o.offer_center_latitude)) * 
                cos(radians(o.offer_center_longitude) - radians(c.longitude)) + 
                sin(radians(c.latitude)) * sin(radians(o.offer_center_latitude))
            )
        ) <= o.max_distance_km THEN 'Available'
        ELSE 'Not Available'
    END AS availability_status
FROM customers c
CROSS JOIN offers o
WHERE o.is_active = 1 AND c.is_active = 1;
