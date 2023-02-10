python src/numerai_signals/load.py\
    --start 221014\
    --end 221022\
    --ticker 000060.KS
    --dev # s3 dev folder
    --local # boto session credential

python src/numerai_signals/load.py\
    --start 221014\
    --end 221022\
    --ntickers 100

python src/numerai_signals/transform.py\
    --cmd volume\
    --lags 5\
    --reload


docker build -t signals_load .

docker run -t signals_load

docker run\
    -v /Users/hugochauvary/Documents/workspace/signals:/home\
    -it local_ubuntu

export AWS_PROFILE=jh_numerai

# docker build --platform=linux/amd64 -t local_ubuntu


aws logs describe-subscription-filters\
    --region eu-west-1\
    --log-group-name SignalsStack-SignalsLogLoad5DA8D8E6-pLhRC1d3Z7Yk

aws logs delete-subscription-filter\
    --region eu-west-1\
    --log-group-name SignalsStack-SignalsLogLoad5DA8D8E6-pLhRC1d3Z7Yk\
    --filter-name Test