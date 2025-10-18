{% snapshot dim_property_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='property_key',
    strategy='timestamp',
    updated_at='scraped_date'
  )
}}

with base as (
  select
    property_type_clean || '|' || room_type_clean || '|' || accommodates as property_key,
    property_type_clean as property_type,
    room_type_clean as room_type,
    accommodates,
    scraped_date_clean as scraped_date,
    created_at,
    updated_at,
    row_number() over (
      partition by property_type_clean, room_type_clean, accommodates, scraped_date_clean
      order by created_at desc, updated_at desc
    ) as rn
  from {{ ref('silver_airbnb_listings') }}
  where property_type_clean is not null and property_type_clean <> ''
    and room_type_clean    is not null and room_type_clean <> ''
    and accommodates is not null and accommodates != '' and accommodates::integer > 0
    and scraped_date_clean is not null
),
latest_per_key as (
  select
    property_type || '|' || room_type || '|' || accommodates as property_key,
    max(scraped_date) as scraped_date
  from base
  group by 1
)

select
  b.property_key,
  b.property_type,
  b.room_type,
  b.accommodates,
  b.scraped_date,
  b.created_at,
  b.updated_at
from base b
join latest_per_key l
  on b.property_key = l.property_key
 and b.scraped_date = l.scraped_date
where b.rn = 1

{% endsnapshot %}