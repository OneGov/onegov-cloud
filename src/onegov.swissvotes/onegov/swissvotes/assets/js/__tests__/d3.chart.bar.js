const jsdom = require('jsdom');
const d3 = require('../d3');
const barChart = require('../d3.chart.bar')(d3);
const data  = {
  "results": [
    {"value": 110.9, "text": "110.9%"},
    {"value": 105, "text": "105%"},
    {"value": 100, "text": "100%"},
    {"value": 100.0, "text": "100.0%"},
    {"value": 99.9, "text": "99.9%"},
    {"value": 88.8, "text": "88.8%"},
    {"value": 50.1, "text": "50.1%"},
    {"value": 50.0, "text": "50.0%"},
    {"value": 50, "text": "50%"},
    {"value": 49.9, "text": "49.9%"},
    {"value": 11.1, "text": "11.1%"},
    {"value": 0.1, "text": "0.1%"},
    {"value": 0.0, "text": "0.0%"},
    {"value": 0, "text": "0%"},
    {"value": -5, "text": "-5%"},
    {"value": -10.9, "text": "-10.9%"},

  ]
};

describe('Bar chart', () => {
  it('renders an empty svg with no data', () => {
    var document = jsdom.jsdom();
    var chart = barChart();
    chart(document.body);
    expect(document.svg(d3)).toMatchSnapshot();
    expect(chart.height()).toBe(0+40);
    expect(chart.width()).toBe(0+20);
  });

  it('renders a svg @0', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 0,
      data: data
    });
    chart(document.body);
    // require('fs').writeFile("bar@0.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(16*24+40);
    expect(chart.width()).toBe(0+20);
  });

  it('renders a svg @100', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 100,
      data: data
    });
    chart(document.body);
    // require('fs').writeFile("bar@100.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(16*24+40);
    expect(chart.width()).toBe(100+20);
  });

  it('renders a svg @500', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 500,
      data: data
    });
    chart(document.body);
    // require('fs').writeFile("bar@500.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(16*24+40);
    expect(chart.width()).toBe(500+20);
  });

  it('renders a svg @700', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: data
    });
    chart(document.body);
    // require('fs').writeFile("bar@700.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(16*24+40);
    expect(chart.width()).toBe(700+20);
  });

  it('renders a svg @2000', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 2000,
      data: data
    });
    chart(document.body);
    // require('fs').writeFile("bar@2000.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(16*24+40);
    expect(chart.width()).toBe(2000+20);
  });

});
