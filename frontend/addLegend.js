// var LEGEND_WIDTH = 800;
// var LEGEND_HEIGHT = 1000;


var LENGEND_GROUP = SVG.append('g')
    .attr("class", "legend-group")
    .attr("transform", "translate(" +(WIDTH-230)+ ", -20)");



LENGEND_GROUP.append("text") 
    .text('Forecasted Sentiment')
    .attr("font-size", "12px");

LENGEND_GROUP.append("text") 
    .text('Predicted Price')
    .attr("y", '15')
    .attr("font-size", "12px");


LENGEND_GROUP.append("text") 
    .text('Predicted Price Bounds')
    .attr("y", '30')
    .attr("font-size", "12px");


LENGEND_GROUP.append("rect")
    .attr('x', -30)
    .attr('y', -4)
    .attr('width', 25)
    .attr('height', 1)
    .attr('stroke', SENTIMENT_COLOR)
    .attr('stroke-dasharray', ("3, 3"))
    .attr('stroke-width', '4px')
    .attr('fill', 'white');

LENGEND_GROUP.append("rect")
    .attr('x', -30)
    .attr('y', 11)
    .attr('width', 25)
    .attr('height', 1)
    .attr('stroke', PRICE_COLOR)
    .attr('stroke-dasharray', ("3, 3"))
    .attr('stroke-width', '4px')
    .attr('fill', 'white');

LENGEND_GROUP.append("rect")
    .attr('x', -30)
    .attr('y', 26)
    .attr('width', 25)
    .attr('height', 1)
    .attr('stroke', UPPER_BOUND_COLOR)
    .attr('stroke-dasharray', ("3, 3"))
    .attr('stroke-width', '2px')
    .attr('fill', 'white');