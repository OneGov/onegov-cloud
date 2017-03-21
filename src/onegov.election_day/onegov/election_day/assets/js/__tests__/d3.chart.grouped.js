const jsdom = require('jsdom');
const d3 = require('../d3');
const groupedChart = require('../d3.chart.grouped')(d3);

const results = [
  {"active": false, "group": "A", "value": {"front": 0, "back": 0}, "item": "1000"},
  {"active": true, "group": "A", "value": {"front": 0, "back": 0}, "item": "2000"},
  {"active": false, "group": "A", "value": {"front": 0, "back": 0}, "item": "3000"},
  {"active": false, "group": "BB", "value": {"front": 1, "back": 1}, "item": "1000"},
  {"active": true, "group": "BB", "value": {"front": 1, "back": 1}, "item": "2000"},
  {"active": false, "group": "BB", "value": {"front": 1, "back": 1}, "item": "3000"},
  {"active": false, "group": "CCC", "value": {"front": 10, "back": 10}, "item": "1000"},
  {"active": true, "group": "CCC", "value": {"front": 10, "back": 10}, "item": "2000"},
  {"active": false, "group": "CCC", "value": {"front": 10, "back": 10}, "item": "3000"},
  {"active": false, "group": "DDDD", "value": {"front": 25, "back": 30}, "item": "1000"},
  {"active": true, "group": "DDDD", "value": {"front": 25, "back": 30}, "item": "2000"},
  {"active": false, "group": "DDDD", "value": {"front": 25, "back": 30}, "item": "3000"},
  {"active": false, "group": "EEEEE", "value": {"front": 50, "back": 40}, "item": "1000"},
  {"active": true, "group": "EEEEE", "value": {"front": 50, "back": 40}, "item": "2000"},
  {"active": false, "group": "EEEEE", "value": {"front": 50, "back": 40}, "item": "3000"},
  {"active": false, "group": "FFFFFF", "value": {"front": 100, "back": 100}, "item": "1000"},
  {"active": true, "group": "FFFFFF", "value": {"front": 100, "back": 100}, "item": "2000"},
  {"active": false, "group": "FFFFFF", "value": {"front": 100, "back": 100}, "item": "3000"},
  {"active": false, "group": "GGGGGGG", "value": {"front": 85.1, "back": 85.7}, "item": "1000"},
  {"active": true, "group": "GGGGGGG", "value": {"front": 85.1, "back": 85.7}, "item": "2000"},
  {"active": false, "group": "GGGGGGG", "value": {"front": 85.1, "back": 85.7}, "item": "3000"},
];

describe('Grouped bar chart', () => {
  it('renders an empty svg with no data', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart();
    chart(document.body);
    expect(document.svg(d3)).toMatchSnapshot();
  });

  it('renders a svg @1', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 1,
      height: 1,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    // require('fs').writeFile("grouped@1.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(1);
    expect(chart.width()).toBe(1);
  });

  it('renders a svg @200', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 200,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    // require('fs').writeFile("grouped@2.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(200);
  });

  it('renders a svg @500', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 500,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    // require('fs').writeFile("grouped@500.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(500);
  });

  it('renders a svg @700', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    // require('fs').writeFile("grouped@700.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg @2000', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 2000,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    // require('fs').writeFile("grouped@2k.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(2000);
  });

  it('renders a svg with wrong more groups and labels as in the data', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": [
          {"active": false, "group": "A", "value": {"front": 0, "back": 0}, "item": "1000"},
          {"active": true, "group": "A", "value": {"front": 0, "back": 0}, "item": "2000"},
          {"active": false, "group": "BB", "value": {"front": 1, "back": 1}, "item": "1000"},
          {"active": true, "group": "BB", "value": {"front": 1, "back": 1}, "item": "2000"},
          {"active": false, "group": "CCC", "value": {"front": 10, "back": 10}, "item": "1000"},
          {"active": true, "group": "CCC", "value": {"front": 10, "back": 10}, "item": "2000"},
          {"active": false, "group": "DDDD", "value": {"front": 25, "back": 30}, "item": "1000"},
          {"active": true, "group": "DDDD", "value": {"front": 25, "back": 30}, "item": "2000"},
        ]}
    });
    chart(document.body);
    // require('fs').writeFile("grouped@w.svg", document.svg());
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(700);
  });

  it('doesn\'t render a svg with missing parameters', () => {
    var document = jsdom.jsdom();
    var chart = groupedChart({
      width: 700,
      data: {
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(400);
    expect(chart.width()).toBe(700);
    var svg = document.svg();

    groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    })(document.body);
    expect(document.svg()).toMatch(svg);

    groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "labels": ["1000", "2000", "3000"],
        "results": results
      }
    })(document.body);
    expect(document.svg()).toMatch(svg);

    groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "results": results
      }
    })(document.body);
    expect(document.svg()).toMatch(svg);

    groupedChart({
      width: 700,
      data: {
        "axis_units": {"front": "f", "back": "b"},
        "maximum": {"front": 100, "back": 100},
        "groups": ["A", "BB", "CCC", "DDDD", "EEEEE", "FFFFFF", "GGGGGGG"],
        "labels": ["1000", "2000", "3000"],
      }
    })(document.body);
    expect(document.svg()).toMatch(svg);
  });
});
