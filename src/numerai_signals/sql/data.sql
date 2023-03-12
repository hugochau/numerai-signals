select
    ticker
    , from_unixtime(timestamp / 1000000000) "timestamp"
    , currency
    , "open"
    , high
    , volume
    , low
    , "close"
from
    "{0}-signals-database"."raw_data"
where
    from_unixtime(timestamp / 1000000000) >= current_date - interval '540' day
group by
    ticker
    , "timestamp"
    , currency
    , "open"
    , high
    , volume
    , low
    , "close"
