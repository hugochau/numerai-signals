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
    "signals"."yahoo"
limit
    1