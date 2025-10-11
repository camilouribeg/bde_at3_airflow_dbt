{% snapshot dim_lga_snapshot %}

{{
    config(
      target_schema='snapshots',
      unique_key='lga_code_2016',
      strategy='timestamp',
      updated_at='created_at',
    )
}}

select
    lga_code_2016,
    male_population,
    female_population,
    total_population,
    male_percentage,
    female_percentage,
    created_at,
    updated_at
from {{ ref('silver_census_g01') }}
where lga_code_2016 is not null
  and total_population > 0

{% endsnapshot %}
