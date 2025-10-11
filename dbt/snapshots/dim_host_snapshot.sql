{% snapshot dim_host_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='host_id',
      strategy='timestamp',
      updated_at='scraped_date',
    )
}}

select
    host_id,
    host_neighbourhood_clean as host_neighbourhood,
    scraped_date,
    current_timestamp as snapshot_created_at
from {{ ref('silver_airbnb_listings') }}
where host_id is not null
  and host_neighbourhood_clean is not null
  and scraped_date is not null

{% endsnapshot %}
can