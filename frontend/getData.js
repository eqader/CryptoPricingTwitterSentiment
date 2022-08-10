var tweetBucketName = 'frontend-public-facing-access';

// Initialize the Amazon Cognito credentials provider
AWS.config.region = 'us-west-1'; // Region
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: 'us-west-1:dc63cda1-73d6-4510-9600-6e85bc5bb636',
});

// Create a new service object
var s3 = new AWS.S3({
  apiVersion: '2006-03-01',
  params: {Bucket: tweetBucketName}
});


async function getCoins() {
  const objects = await s3
    .listObjects({})
    .promise();

    let coins = objects.Contents.map(function(file) {
      return file.Key.split('.')[0];
    });

  coins = coins.filter(function(x) {
      return x.includes('coins') && x !== 'coins/';
  });

  coins = coins.map(function(file) {
    return file.split('/')[1];
  });

  return coins;
}

async function getCoinData(coin) {
  var params = {
    Bucket: tweetBucketName, 
    Key: 'coins/' + coin + '.csv',
    ResponseContentType: 'text/plain'
  };

  const object = await s3
    .getObject(params)
    .promise();

  return object.Body.toString('utf-8');
}


async function getSentimentPredictionData(coin) {
  var params = {
    Bucket: tweetBucketName, 
    Key: 'predictions_with_sentiment/' + coin + '.csv',
    ResponseContentType: 'text/plain'
  };

  const object = await s3
    .getObject(params)
    .promise();

  return object.Body.toString('utf-8');
}
