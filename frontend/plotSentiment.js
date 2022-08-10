var MARGIN = {top: 30, right: 50, bottom: 50, left: 70};
var WIDTH = 960 - MARGIN.left - MARGIN.right;
var HEIGHT = 500 - MARGIN.top - MARGIN.bottom;


var PRICE_COLOR = '#1f77b4'
var SENTIMENT_COLOR = '#ff7f0e'
var UPPER_BOUND_COLOR ='#7f7f7f'
var LOWER_BOUND_COLOR ='#7f7f7f'


var SVG = d3.select("#plot")
  .append("svg")
  .attr("width", WIDTH + MARGIN.left + MARGIN.right)
  .attr("height", HEIGHT + MARGIN.top + MARGIN.bottom)
  .attr("id", "svg")
  .append("g")
  .attr("class", "plot-a")
  .attr("id", "plot-a")
  .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")");

var TWEET_SVG = d3.select("#tweets")
  .append("svg")
  .attr("width", WIDTH + MARGIN.left + MARGIN.right + 400)
  .attr("height", HEIGHT + MARGIN.top + MARGIN.bottom)
  .attr("id", "svg")
  .append("g")
  .attr("class", "tweetg")
  .attr("id", "tweetg");

var LINES_GROUP = SVG.append('g')
  .attr("class", "lines-a")
  .attr("id", "lines-a")


var X_SCALE = d3.scaleTime()
  .range([0, WIDTH]);


var Y_SCALE_SENTIMENT = d3.scaleLinear()
  .domain([-1, 1])
  .range([HEIGHT, 0]);


var Y_SCALE_PRICE = d3.scaleLinear()
  .range([HEIGHT, 0]);


SVG.append("text")
  .attr("class", "x_axis_label")
  .attr("id", "x_axis_label")
  .attr("transform", "translate("+WIDTH/2+", "+(HEIGHT + 40)+")")
  .attr("text-anchor", "middle")
  .style("fill", "black")
  .attr("font-size", "25px")
  .text("Date");


var Y_AXIS_SENTIMENT = d3.axisLeft(Y_SCALE_SENTIMENT)  
  .ticks(10);


SVG.append("g")
  .attr("class", "y-axis-sentiment")
  .attr("id", "y-axis-sentiment")
  .call(Y_AXIS_SENTIMENT);


SVG.append("text")
  .attr("class", "y-axis-sentiment-label")
  .attr("text-anchor", "end")
  .attr("transform", "translate(-30 ,"+(HEIGHT/2 - 60)+"), rotate(270)")
  .text("User Sentiment")
  .attr("id", "y-axis-sentiment-label");


SVG.append("text")
  .attr("class", "y-axis-price-label")
  .attr("text-anchor", "end")
  .attr("transform", " translate(" + (WIDTH + 30) + ","+(HEIGHT/2 + 20)+"), rotate(90)")
  .text("Price")
  .attr("id", "y-axis-price-label");


var SYM = SVG.append("g")
  .attr("class", "symbols")
  .attr("id", "symbols");



var PARSE_DATE = d3.timeParse('%Y-%m-%d');
var PARSE_PREDICTION_DATE = d3.timeParse('%Y-%m-%d');
var COINS = getCoins();


Promise.all([COINS])
  .then(function(values){  
    populateDropDown(null, values[0]);
  });


function populateDropDown(error, coinList) {

  var dropDown = d3.select("#coinDropdown");
  var radioButton = d3.select("#sentiment_prediction");

  dropDown.selectAll("option")
    .data(coinList)
    .enter()
    .append("option")
    .attr("value", function(coin) { return coin; })
    .text(function(coin) { return coin; });

  dropDown.on("change", function() {
    let dropDownSelection = d3.event.target.value;
    let radioValue = document.querySelector('input[name="sentiment_prediction"]:checked').value;

    console.log(radioValue)
    console.log(dropDownSelection);

    populateChart(dropDownSelection, radioValue);
  });

  radioButton.on("change", function() {
    let radioValue = d3.event.target.value;
    let dropDownSelection = dropDown.node().value; 

    console.log(radioValue)
    console.log(dropDownSelection);

    populateChart(dropDownSelection, radioValue);
  });

  // initialize
  let radioValue = document.querySelector('input[name="sentiment_prediction"]:checked').value;
  let dropDownSelection = dropDown.node().value; 
  populateChart(dropDownSelection, radioValue);

}


function populateChart(coin, sentimentPrediction) {

  getCoinData(coin).then(rawCoinData => {
    getSentimentPredictionData(coin).then(rawPredictionData => {

    const coinHistoricalData = parseCoinData(rawCoinData);
    const coinPredictionData = parsePredictionData(rawPredictionData, sentimentPrediction);

    adjustScale(coinHistoricalData, coinPredictionData);

    addSentimentLine(coinHistoricalData);
    addPriceLine(coinHistoricalData);

    addPredictionSentimentLine(coinPredictionData);
    addPredictionPriceLine(coinPredictionData)

    addPredictionPriceUpperBound(coinPredictionData);
    addPredictionPriceLowerBound(coinPredictionData);

    // refreshSymbols();
    addSentSymbols(coinHistoricalData);
    addPriceSymbols(coinHistoricalData);

    }).catch(err => {
      console.log(err)
    });

  }).catch(err => {
    console.log(err)
  });

}


function parseCoinData(coinData){
  let data = d3.csvParse(coinData, function (d) {
    return {
      date: PARSE_DATE(d.Day),
      sentiment: +d["sentiment"],
      tweet1: 'Tweet 1 - ' + d.sample_tweet1,
      tweet2: 'Tweet 2 - ' + d.sample_tweet2,
      tweet3: 'Tweet 3 - ' + d.sample_tweet3,
      tweet4: 'Tweet 4 - ' + d.sample_tweet4,
      tweet5: 'Tweet 5 - ' + d.sample_tweet5,
      price: +d["Price"],
    }
  });
  console.log(data);
  return data;
}


function parsePredictionData(predictionData, predictedSentiment){
  let data = d3.csvParse(predictionData, function (d) {
    return {
      date: PARSE_PREDICTION_DATE(d.Date),
      sentiment: +d[`${predictedSentiment}_sentiment`],
      upper: +d[`${predictedSentiment}_upper_price`],
      lower: filter_lower_bound(+d[`${predictedSentiment}_lower_price`]),
      price: +d[`${predictedSentiment}_predictions`],
    }
  });
  //console.log(data);
  return data;
}


function filter_lower_bound(lowerBound){
  if(lowerBound < 0){
    return 0;
  }
  return lowerBound;
}


function adjustScale(coinData, predictionData){
  d3.select('.x-axis').remove();

  let coinDates = d3.extent(coinData, function(d) {return d.date;});
  let predictionDates = d3.extent(predictionData, function(d) {return d.date;});

  X_SCALE.domain(d3.extent(coinDates.concat(predictionDates), function(d) {return d;}));

  let xAxis = d3.axisBottom(X_SCALE)
    .ticks(10)
    .tickFormat(d3.timeFormat("%b %y"));

  SVG.append("g")
    .attr("class", "x-axis")
    .attr("id", "x-axis")
    .attr("transform", "translate(0, " + HEIGHT+")")
    .call(xAxis);

  d3.select('.y-axis-price').remove();

  let coinPrices = d3.extent(coinData, function(d) {return d.price;});
  let predictionPrices = d3.extent(predictionData, function(d) {return d.price;});
  let upperBoundPrices = d3.extent(predictionData, function(d) {return d.upper;});
  let lowerBoundPrices = d3.extent(predictionData, function(d) {return d.lower;});

  Y_SCALE_PRICE.domain(d3.extent(coinPrices.concat(predictionPrices, upperBoundPrices, lowerBoundPrices), function(d) {return d;}));

  let yAxisPrice = d3.axisRight(Y_SCALE_PRICE)
    .ticks(10);

  SVG.append("g")
    .attr("class", "y-axis-price")
    .attr("id", "y-axis-price")
    .attr("transform", "translate(" + (WIDTH) + ",0)")
    .call(yAxisPrice);

}


function addSentimentLine(data){
  d3.select('.lines-sentiment').remove();

  let sentimentLineScale = d3.line()
    .x(function(d) {return X_SCALE(d.date);})
    .y(function(d) { return Y_SCALE_SENTIMENT(d.sentiment);});

  LINES_GROUP.append("path")
    .attr("class", "lines-sentiment")
    .attr("d", sentimentLineScale(data))
    .attr("fill", "none")
    .style("stroke", SENTIMENT_COLOR);

}


function addPriceLine(data){
  d3.select('.lines-price').remove();

  let priceLineScale = d3.line()
    .x(function(d) {return X_SCALE(d.date);})
    .y(function(d) { return Y_SCALE_PRICE(d.price);});

  LINES_GROUP.append("path")
    .attr("class", "lines-price")
    .attr("d", priceLineScale(data))
    .attr("fill", "none")
    .style("stroke", PRICE_COLOR);
}


function addPredictionPriceLine(data){
  d3.select('.lines-prediction-price').remove();

  let priceLineScale = d3.line()
    .x(function(d) {return X_SCALE(d.date);})
    .y(function(d) { return Y_SCALE_PRICE(d.price);});

  LINES_GROUP.append("path")
    .attr("class", "lines-prediction-price")
    .attr("d", priceLineScale(data))
    .attr("fill", "none")
    .style("stroke-dasharray", ("3, 3")) 
    .style('stroke-width', '4px')
    .style("stroke", PRICE_COLOR);
}


function addPredictionPriceUpperBound(data){
  d3.select('.lines-prediction-upper-bound').remove();

  let priceLineScale = d3.line()
    .x(function(d) {return X_SCALE(d.date);})
    .y(function(d) { return Y_SCALE_PRICE(d.upper);});

  LINES_GROUP.append("path")
    .attr("class", "lines-prediction-upper-bound")
    .attr("d", priceLineScale(data))
    .attr("fill", "none")
    .style("stroke-dasharray", ("3, 3")) 
    .style('stroke-width', '2px')
    .style("stroke", UPPER_BOUND_COLOR);
}


function addPredictionPriceLowerBound(data){
  d3.select('.lines-prediction-lower-bound').remove();

  let priceLineScale = d3.line()
    .x(function(d) {return X_SCALE(d.date);})
    .y(function(d) { return Y_SCALE_PRICE(d.lower);});

  LINES_GROUP.append("path")
    .attr("class", "lines-prediction-lower-bound")
    .attr("d", priceLineScale(data))
    .attr("fill", "none")
    .style("stroke-dasharray", ("3, 3")) 
    .style('stroke-width', '2px')
    .style("stroke", LOWER_BOUND_COLOR);
}


function addPredictionSentimentLine(data){
    d3.select('.lines-prediction-sentiment').remove();
  
    let sentimentLineScale = d3.line()
      .x(function(d) {return X_SCALE(d.date);})
      .y(function(d) { return Y_SCALE_SENTIMENT(d.sentiment);});
  
    LINES_GROUP.append("path")
      .attr("class", "lines-prediction-sentiment")
      .attr("d", sentimentLineScale(data))
      .attr("fill", "none")
      .style("stroke-dasharray", ("3, 3")) 
      .style('stroke-width', '4px')
      .style("stroke", SENTIMENT_COLOR);
  
  }


function addPriceSymbols(data){
  d3.selectAll('.sym-price').remove();

  console.log(data[0].price)
  //console.log(data.sentiment)

  for (var i = 0; i < data.length; i++){
  
    SYM.append("circle")
      .attr("class", "sym-price")
      .attr("id", "sym-price")
      .attr("cx", X_SCALE(data[i].date))
      .attr("cy", Y_SCALE_PRICE(data[i].price))
      .attr("date", 'Date:' + data[i].date.toLocaleDateString("en-US"))
      .attr("dp", 'Price: ' + data[i].price)
      .attr("tweets1", data[i].tweet1)
      .attr("tweets2", data[i].tweet2)
      .attr("tweets3", data[i].tweet3)
      .attr("tweets4", data[i].tweet4)
      .attr("tweets5", data[i].tweet5)
      .attr("r", 3)
      .style("fill", PRICE_COLOR)
      .on("mouseover", handleMouseOver)
      .on("mouseout", handleMouseOut);

 } 
}


function addSentSymbols(data){

  d3.selectAll('.sym-sentiment').remove();
  
  //console.log(data[0].sentiment)
  //console.log(data.sentiment)

   for (var i = 0; i < data.length; i++){
    
    SYM.append("circle")
      .attr("class", "sym-sentiment")
      .attr("id", "sym-sentiment")
      .attr("cx", X_SCALE(data[i].date))
      .attr("cy", Y_SCALE_SENTIMENT(data[i].sentiment))
      .attr("r", 3)
      .attr("date", 'Date:' + data[i].date.toLocaleDateString("en-US"))
      .attr("dp", 'Sentiment: ' + data[i].sentiment.toFixed(2))
      .attr("tweets1", data[i].tweet1)
      .attr("tweets2", data[i].tweet2)
      .attr("tweets3", data[i].tweet3)
      .attr("tweets4", data[i].tweet4)
      .attr("tweets5", data[i].tweet5)
      .style("fill", SENTIMENT_COLOR)
      .on("mouseover", handleMouseOver)
      .on("mouseout", handleMouseOut);

    }
}

function handleMouseOver(d, i) {  // Add interactivity

  // Make the size bigger
  d3.select(this)
    .attr("r", 10);

  SVG.append("rect")
    .attr("class", "sym-text")
    .attr("x", parseFloat(d3.select(this).attr("cx")) + 10)
    .attr("y", parseFloat(d3.select(this).attr("cy")) - 35)
    .attr('width', 90)
    .attr('height', 30)
    .style('fill', 'white');

  SVG.append("text")
    .attr("class", "sym-text")
    .attr("x", parseFloat(d3.select(this).attr("cx")) + 10)
    .attr("y", parseFloat(d3.select(this).attr("cy")) - 20)
    .attr("font-size", "12px")
    .style("font-weight", 'bold')
    .style('background-color', 'white')
    .text(d3.select(this).attr("date"));

  SVG.append("text")
    .attr("class", "sym-text")
    .attr("x", parseFloat(d3.select(this).attr("cx")) + 10)
    .attr("y", parseFloat(d3.select(this).attr("cy")) - 10)
    .attr("font-size", "12px")
    .style('background-color', 'white')
    .style("font-weight", 'bold')
    .text(d3.select(this).attr("dp"));

    
  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text("Tweets from that Day")
    .attr("y", 30)
    .attr("x", 550)
    .attr("font-size", "35px");
  
  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text(d3.select(this).attr("tweets1"))
    .attr("y", 70)
    
  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text(d3.select(this).attr("tweets2"))
    .attr("y", 100);

  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text(d3.select(this).attr("tweets3"))
    .attr("y", 130);
  
  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text(d3.select(this).attr("tweets4"))
    .attr("y", 160);
  
  TWEET_SVG.append("text")
    .attr("class", "sym-tweet")
    .text(d3.select(this).attr("tweets5"))
    .attr("y", 190);
}

function handleMouseOut(d, i) {
  // Return to normal size
  d3.select(this).attr("r",3);
  d3.selectAll('.sym-text').remove();
  d3.selectAll('.sym-tweet').remove();
  
  }