{% snapshot dim_neighbourhood_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='neighbourhood_key',
      strategy='timestamp',
      updated_at='scraped_date',
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['listing_neighbourhood_clean', 'host_neighbourhood_clean']) }} as neighbourhood_key,
    listing_neighbourhood_clean as listing_neighbourhood,
    host_neighbourhood_clean as host_neighbourhood,
    scraped_date,
    current_timestamp as snapshot_created_at
from {{ ref('silver_airbnb_listings') }}
where listing_neighbourhood_clean is not null
  and host_neighbourhood_clean is not null
  and scraped_date is not null

{% endsnapshot %}
