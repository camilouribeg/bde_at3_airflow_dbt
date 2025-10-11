{{
    config(
        unique_key='lga_code_2016',
        alias='bronze_census_g02'
    )
}}

select * from {{ source('raw', 'raw_census_g02') }}
