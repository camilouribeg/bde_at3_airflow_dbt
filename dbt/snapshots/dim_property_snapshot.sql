{% snapshot dim_property_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='property_key',
      strategy='timestamp',
      updated_at='scraped_date',
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['property_type_clean', 'room_type_clean', 'accommodates']) }} as property_key,
    property_type_clean as property_type,
    room_type_clean as room_type,
    accommodates,
    scraped_date,
    current_timestamp as snapshot_created_at
from {{ ref('silver_airbnb_listings') }}
where property_type_clean is not null
  and room_type_clean is not null
  and accommodates is not null
  and accommodates > 0
  and scraped_date is not null

{% endsnapshot %}
