{{
    config(
        unique_key='listing_id',
        alias='bronze_airbnb_listings'
    )
}}

select * from {{ source('raw', 'raw_airbnb_listings') }}
