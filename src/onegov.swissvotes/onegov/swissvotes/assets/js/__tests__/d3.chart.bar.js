const jsdom = require('jsdom');
const d3 = require('../d3');
const barChart = require('../d3.chart.bar')(d3);
const data  = {
  "results": [
    {"text": "110.9%", "yea": 110.9, "none": 0, "nay": -10.9},
    {"text": "105%", "yea": 105, "none": 0, "nay": -5},
    {"text": "100%", "yea": 100, "none": 0, "nay": 0},
    {"text": "100.0%", "yea": 100.0, "none": 0.0, "nay": 0},
    {"text": "99.9%", "yea": 99.9, "none": 0.1, "nay": 0},
    {"text": "88.8%", "yea": 88.8, "none": 11.2, "nay": 0},
    {"text": "50.1%", "yea": 50.1, "none": 49.9, "nay": 0},
    {"text": "50.0%", "yea": 50.0, "none": 50.0, "nay": 0},
    {"text": "50%", "yea": 50, "none": 50, "nay": 0},
    {"text": "49.9%", "yea": 49.9, "none": 50.1, "nay": 0},
    {"text": "11.1%", "yea": 11.1, "none": 88.9, "nay": 0},
    {"text": "0.1%", "yea": 0.1, "none": 99.9, "nay": 0},
    {"text": "0.0%", "yea": 0.0, "none": 100.0, "nay": 0},
    {"text": "0%", "yea": 0, "none": 100, "nay": 0},
    {"text": "-5%", "yea": -5, "none": 105, "nay": 0},
    {"text": "-10.9%", "yea": -10.9, "none": 110.9, "nay": 0},

    {"text": "", "yea": 0, "none": 0, "nay": 0},

    {"text": "8 0 0", "yea": 100.0, "none": 0.0, "nay": 0.0},
    {"text": "6 1 1", "yea": 75.0, "none": 12.5, "nay": 12.5},
    {"text": "4 2 2", "yea": 50.0, "none": 25.0, "nay": 25.0},
    {"text": "2 3 3", "yea": 25.0, "none": 37.5, "nay": 37.5},
    {"text": "0 4 4", "yea": 0.0, "none": 50.0, "nay": 50.0},
    {"text": "0 2 6", "yea": 0.0, "none": 25.0, "nay": 75.0},
    {"text": "0 0 8", "yea": 0.0, "none": 0.0, "nay": 100.0},

    {"text": "", "yea": 0, "none": 0, "nay": 0},

    {"text": "111", "yea": true, "none": true, "nay": true},
    {"text": "110", "yea": true, "none": true, "nay": 0},
    {"text": "101", "yea": true, "none": 0, "nay": true},
    {"text": "100", "yea": true, "none": 0, "nay": 0},
    {"text": "011", "yea": 0, "none": true, "nay": true},
    {"text": "010", "yea": 0, "none": true, "nay": 0},
    {"text": "001", "yea": 0, "none": 0, "nay": true},
    {"text": "000", "yea": 0, "none": 0, "nay": 0},

    {"text": "", "yea": 0, "nay": 0, "none": 0},

    {
        "text": "111", "text_label": "text label",
        "yea": true, "yea_label": "yea label",
        "none": true, "none_label": "none label",
        "nay": true, "nay_label": "nay label"
    },
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
    require('fs').writeFile("bar@0.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(35*26+40);
    expect(chart.width()).toBe(0+20);
  });

  it('renders a svg @100', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 100,
      data: data
    });
    chart(document.body);
    require('fs').writeFile("bar@100.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(35*26+40);
    expect(chart.width()).toBe(100+20);
  });

  it('renders a svg @500', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 500,
      data: data
    });
    chart(document.body);
    require('fs').writeFile("bar@500.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(35*26+40);
    expect(chart.width()).toBe(500+20);
  });

  it('renders a svg @700', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: data
    });
    chart(document.body);
    require('fs').writeFile("bar@700.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(35*26+40);
    expect(chart.width()).toBe(700+20);
  });

  it('renders a svg @2000', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 2000,
      data: data
    });
    chart(document.body);
    require('fs').writeFile("bar@2000.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(35*26+40);
    expect(chart.width()).toBe(2000+20);
  });

});
