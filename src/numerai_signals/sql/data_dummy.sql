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
    "615955932111-signals-database"."raw_data"
limit
    1