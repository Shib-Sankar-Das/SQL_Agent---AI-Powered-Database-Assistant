-- Sample data for testing

-- Insert sample customers with location data
INSERT OR IGNORE INTO customers (first_name, last_name, email, phone, registration_date, city, state, country, postal_code, latitude, longitude, is_active) VALUES
('John', 'Doe', 'john.doe@email.com', '+1-555-0101', '2024-01-15', 'New York', 'NY', 'USA', '10001', 40.7589, -73.9851, 1),
('Jane', 'Smith', 'jane.smith@email.com', '+1-555-0102', '2024-02-20', 'Los Angeles', 'CA', 'USA', '90210', 34.0522, -118.2437, 1),
('Mike', 'Johnson', 'mike.johnson@email.com', '+1-555-0103', '2024-03-10', 'Chicago', 'IL', 'USA', '60601', 41.8781, -87.6298, 1),
('Sarah', 'Williams', 'sarah.williams@email.com', '+1-555-0104', '2024-04-05', 'Houston', 'TX', 'USA', '77001', 29.7604, -95.3698, 1),
('David', 'Brown', 'david.brown@email.com', '+1-555-0105', '2024-05-12', 'Phoenix', 'AZ', 'USA', '85001', 33.4484, -112.0740, 1),
('Emily', 'Davis', 'emily.davis@email.com', '+1-555-0106', '2024-06-18', 'Philadelphia', 'PA', 'USA', '19101', 39.9526, -75.1652, 1),
('Chris', 'Wilson', 'chris.wilson@email.com', '+1-555-0107', '2024-07-03', 'San Antonio', 'TX', 'USA', '78201', 29.4241, -98.4936, 0),
('Lisa', 'Taylor', 'lisa.taylor@email.com', '+1-555-0108', '2024-01-25', 'San Diego', 'CA', 'USA', '92101', 32.7157, -117.1611, 1),
('Tom', 'Anderson', 'tom.anderson@email.com', '+1-555-0109', '2024-02-14', 'Dallas', 'TX', 'USA', '75201', 32.7767, -96.7970, 1),
('Amy', 'Thomas', 'amy.thomas@email.com', '+1-555-0110', '2024-03-22', 'San Jose', 'CA', 'USA', '95101', 37.3382, -121.8863, 1);

-- Insert sample offers with location data
INSERT OR IGNORE INTO offers (offer_name, description, price, duration_months, available_cities, available_states, available_countries, is_location_specific, max_distance_km, offer_center_latitude, offer_center_longitude, is_active) VALUES
('Basic Plan', 'Basic subscription with essential features', 9.99, 1, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Standard Plan', 'Standard subscription with additional features', 19.99, 1, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Premium Plan', 'Premium subscription with all features', 29.99, 1, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Annual Basic', 'Annual basic plan with discount', 99.99, 12, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Annual Standard', 'Annual standard plan with discount', 199.99, 12, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Annual Premium', 'Annual premium plan with discount', 299.99, 12, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Student Discount', 'Special student pricing', 4.99, 1, 'New York,Los Angeles,Chicago,Boston', 'NY,CA,IL,MA', 'USA', 1, NULL, NULL, NULL, 1),
('Family Plan', 'Plan for up to 4 family members', 39.99, 1, NULL, 'CA,TX,NY', 'USA', 1, NULL, NULL, NULL, 1),
('Business Basic', 'Basic business plan', 49.99, 1, 'New York,San Francisco,Seattle,Austin', 'NY,CA,WA,TX', 'USA', 1, NULL, NULL, NULL, 1),
('Enterprise', 'Enterprise solution with custom features', 99.99, 1, NULL, NULL, 'USA', 0, NULL, NULL, NULL, 1),
('Local NYC Special', 'Special offer for NYC area customers', 14.99, 1, 'New York', 'NY', 'USA', 1, 50, 40.7589, -73.9851, 1),
('California Exclusive', 'Exclusive offer for California residents', 24.99, 3, NULL, 'CA', 'USA', 1, NULL, NULL, NULL, 1);

-- Insert sample subscriptions
INSERT OR IGNORE INTO subscriptions (customer_id, offer_id, start_date, end_date, status, payment_amount) VALUES
(1, 1, '2024-01-15', '2024-02-15', 'expired', 9.99),
(1, 2, '2024-02-15', '2024-03-15', 'expired', 19.99),
(1, 4, '2024-03-15', '2025-03-15', 'active', 99.99),
(2, 2, '2024-02-20', '2024-03-20', 'expired', 19.99),
(2, 5, '2024-03-20', '2025-03-20', 'active', 199.99),
(3, 1, '2024-03-10', '2024-04-10', 'expired', 9.99),
(3, 3, '2024-04-10', '2024-05-10', 'cancelled', 29.99),
(4, 7, '2024-04-05', '2024-05-05', 'expired', 4.99),
(4, 3, '2024-05-05', '2024-06-05', 'active', 29.99),
(5, 2, '2024-05-12', '2024-06-12', 'active', 19.99),
(6, 8, '2024-06-18', '2024-07-18', 'active', 39.99),
(7, 1, '2024-07-03', '2024-08-03', 'cancelled', 9.99),
(8, 6, '2024-01-25', '2025-01-25', 'active', 299.99),
(9, 2, '2024-02-14', '2024-03-14', 'expired', 19.99),
(9, 9, '2024-03-14', '2024-04-14', 'active', 49.99),
(10, 3, '2024-03-22', '2024-04-22', 'active', 29.99);
