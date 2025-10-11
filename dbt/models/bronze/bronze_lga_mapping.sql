{{
    config(
        unique_key='lga_name',
        alias='bronze_lga_mapping'
    )
}}

select * from {{ source('raw', 'raw_lga_mapping') }}
