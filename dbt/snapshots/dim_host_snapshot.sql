{% snapshot dim_host_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='host_id',
    strategy='timestamp',
    updated_at='scraped_date_clean'
  )
}}
with base as (
  select
    listing_id,
    host_id,
    host_neighbourhood_clean as host_neighbourhood,
    scraped_date_clean as scraped_date,
    created_at,
    updated_at,
    row_number() over (
      partition by host_id, scraped_date
      order by created_at desc, updated_at desc, listing_id
    ) as rn
  from {{ ref('silver_airbnb_listings') }}
  where host_id is not null
    and host_neighbourhood_clean is not null
    and host_neighbourhood_clean <> ''
    and scraped_date_clean is not null
),
-- ensure ONE row per host_id per run: keep only the latest scrape per host
latest_per_host as (
  select host_id, max(scraped_date_clean) as scraped_date
  from base
  group by host_id
)
select 
  b.host_id,
  b.host_neighbourhood,
  b.scraped_date,
  b.created_at,
  b.updated_at
from base b
join latest_per_host l
  on b.host_id = l.host_id
 and b.scraped_date = l.scraped_date
where b.rn = 1
{% endsnapshot %}