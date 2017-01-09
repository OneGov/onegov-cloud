const jsdom = require('jsdom');
var d3 = require('../d3');
require('../d3.sankey')(d3);
const sankeyChart = require('../d3.chart.sankey')(d3);

const data = {
  "nodes": [
    {"active": true, "id": 0, "display_value": "0", "name": "0"},
    {"active": false, "id": 1, "display_value": "1", "name": "1"},
    {"active": true, "id": 2, "display_value": "2", "name": "2"},
    {"active": false, "id": 3, "display_value": "3", "name": "3"},
    {"active": true, "id": 4, "display_value": "4", "name": "4"},
    {"active": false, "id": 5, "display_value": "5", "name": "5"},
    {"active": false, "id": 6, "display_value": "6", "name": "6"},
    {"active": false, "id": 7, "display_value": "7", "name": "7"},
    {"active": false, "id": 8, "display_value": "8", "name": "8"},
    {"active": false, "id": 9, "display_value": "9", "name": "9"},
  ],
  "links":[
    {"source": 0, "target": 2, "value": 10},
    {"source": 1, "target": 2, "value": 10},
    {"source": 2, "target": 4, "value": 20},
    {"source": 3, "target": 4, "value": 10},
    {"source": 5, "target": 6, "value": 10},
    {"source": 7, "target": 9, "value": 10},
    {"source": 8, "target": 9, "value": 10},
  ]
};

describe('Sankey bar chart', () => {
  it('renders an empty svg with no data', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart();
    chart(document.body);
    expect(document.svg(d3)).toMatchSnapshot();
  });

  it('renders a svg @1', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 1,
      data: data
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(1);
  });

  it('renders a svg @200', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 200,
      data: data
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(200);
  });

  it('renders a svg @500', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 500,
      data: data
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(500);
  });

  it('renders a svg @700', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 700,
      data: data
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg @2000', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 2000,
      data: data
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(2000);
  });

  it('renders a svg with four levels', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      width: 700,
      data: {
        "nodes": [
          {"active": true, "id": 0, "display_value": "0", "name": "0"},
          {"active": false, "id": 1, "display_value": "1", "name": "1"},
          {"active": true, "id": 2, "display_value": "2", "name": "2"},
          {"active": false, "id": 3, "display_value": "3", "name": "3"},
          {"active": true, "id": 4, "display_value": "4", "name": "4"},
          {"active": false, "id": 5, "display_value": "5", "name": "5"},
          {"active": true, "id": 6, "display_value": "6", "name": "6"},
        ],
        "links":[
          {"source": 0, "target": 2, "value": 10},
          {"source": 1, "target": 2, "value": 10},
          {"source": 2, "target": 4, "value": 20},
          {"source": 3, "target": 4, "value": 10},
          {"source": 4, "target": 6, "value": 30},
          {"source": 5, "target": 6, "value": 10},
        ]
      }
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(700);
  });

  it('renders an inverse svg with four levels', () => {
    var document = jsdom.jsdom();
    var chart = sankeyChart({
      inverse: true,
      width: 700,
      data: {
        "nodes": [
          {"active": true, "id": 0, "display_value": "0", "name": "0"},
          {"active": false, "id": 1, "display_value": "1", "name": "1"},
          {"active": true, "id": 2, "display_value": "2", "name": "2"},
          {"active": false, "id": 3, "display_value": "3", "name": "3"},
          {"active": true, "id": 4, "display_value": "4", "name": "4"},
          {"active": false, "id": 5, "display_value": "5", "name": "5"},
          {"active": true, "id": 6, "display_value": "6", "name": "6"},
        ],
        "links":[
          {"source": 0, "target": 2, "value": 10},
          {"source": 1, "target": 2, "value": 10},
          {"source": 2, "target": 4, "value": 20},
          {"source": 3, "target": 4, "value": 10},
          {"source": 4, "target": 6, "value": 30},
          {"source": 5, "target": 6, "value": 10},
        ]
      }
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(720);
    expect(chart.width()).toBe(700);
  });
});
