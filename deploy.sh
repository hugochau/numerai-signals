# exit when any command fails
set -e

# build python app
make all
coverage run -m pytest -v && coverage report -m

if [ "$1" == "dev" ];
then
    # dev account cdk deploy
    export AWS_PROFILE=numerai_dev

else
    # prod account pseudo CI/CD pipeline
    export AWS_PROFILE=numerai

    git add -A
    git commit -am "$1"
    git push
fi

# build/deploy cdk app
# npm install
# npm ci
# npm run build
# npx cdk synth
cdk diff
cdk deploy --force
