# :arg $1 ntickers: how many tickers to load
# :arg $2 local [optional]: credential based AWS connection

# checking machine type because
# date function has different syntax on mac
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

if [ ${machine} == "Mac" ];
then
    start_date=$(date -v -2d '+%y%m%d')
else
    start_date=$(date -d '2 days ago' '+%y%m%d')
fi

end_date=$(date '+%y%m%d')

if [ ${machine} == "Linux" -a "$2" == "local" ];
then
    # running inside local linux container
    # requires aws credential solution
    python3 src/numerai_signals/load.py\
        --start $start_date\
        --end $end_date\
        --ntickers $1\
        --local

# elif [ ${machine} == "Mac" ];
# then
#     # running inside local linux container
#     # requires aws credential solution
#     python3 src/numerai_signals/load.py\
#         --start $start_date\
#         --end $end_date\
#         --ntickers $1

else
    python3 src/numerai_signals/load.py\
        --start $start_date\
        --end $end_date\
        --ntickers $1
fi
