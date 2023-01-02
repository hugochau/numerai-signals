# exit when any command fails
set -e

# build project
make copy

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

npm install
npm ci
npm run build
npx cdk synth
cdk deploy --force
