{% snapshot dim_neighbourhood_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='neighbourhood_key',
    strategy='timestamp',
    updated_at='scraped_date'
  )
}}

with base as (
  select
    (listing_neighbourhood_clean || '|' || host_neighbourhood_clean) as neighbourhood_key,
    listing_neighbourhood_clean as listing_neighbourhood,
    host_neighbourhood_clean   as host_neighbourhood,
    scraped_date,
    created_at,
    updated_at,
    row_number() over (
      partition by listing_neighbourhood_clean, host_neighbourhood_clean, scraped_date
      order by created_at desc, updated_at desc
    ) as rn
  from {{ ref('silver_airbnb_listings') }}
  where listing_neighbourhood_clean is not null and listing_neighbourhood_clean <> ''
    and host_neighbourhood_clean    is not null and host_neighbourhood_clean <> ''
    and scraped_date is not null
),
latest_per_key as (
  select
    (listing_neighbourhood_clean || '|' || host_neighbourhood_clean) as neighbourhood_key,
    max(scraped_date) as scraped_date
  from {{ ref('silver_airbnb_listings') }}
  where listing_neighbourhood_clean is not null and listing_neighbourhood_clean <> ''
    and host_neighbourhood_clean    is not null and host_neighbourhood_clean <> ''
    and scraped_date is not null
  group by 1
)

select
  b.neighbourhood_key,
  b.listing_neighbourhood,
  b.host_neighbourhood,
  b.scraped_date,
  b.created_at,
  b.updated_at
from base b
join latest_per_key l
  on b.neighbourhood_key = l.neighbourhood_key
 and b.scraped_date      = l.scraped_date
where b.rn = 1

{% endsnapshot %}
