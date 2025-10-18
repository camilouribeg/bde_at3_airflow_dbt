-- Drop the existing table
DROP TABLE IF EXISTS bronze.raw_airbnb_listings;

-- Create the corrected table matching your actual CSV structure
CREATE TABLE bronze.raw_airbnb_listings (
    listing_id BIGINT,
    scrape_id BIGINT,
    scraped_date VARCHAR(50),
    host_id BIGINT,
    host_name VARCHAR(255),
    host_since VARCHAR(50),
    host_is_superhost BOOLEAN,
    host_neighbourhood VARCHAR(255),
    listing_neighbourhood VARCHAR(255),
    property_type VARCHAR(100),
    room_type VARCHAR(50),
    accommodates INTEGER,
    price DECIMAL(10,2),
    has_availability BOOLEAN,
    availability_30 INTEGER,
    number_of_reviews INTEGER,
    review_scores_rating DECIMAL(3,2),
    review_scores_accuracy DECIMAL(3,2),
    review_scores_cleanliness DECIMAL(3,2),
    review_scores_checkin DECIMAL(3,2),
    review_scores_communication DECIMAL(3,2),
    review_scores_value DECIMAL(3,2),
    PRIMARY KEY (listing_id)
);
