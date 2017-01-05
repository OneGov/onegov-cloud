const jsdom = require('jsdom');
const d3 = require('../d3');
const barChart = require('../d3.chart.bar')(d3);

describe('Bar chart', () => {
  it('renders an empty svg with no data', () => {
    var document = jsdom.jsdom();
    var chart = barChart();
    chart(document.body);
    expect(document.svg(d3)).toMatchSnapshot();
    expect(chart.height()).toBe(0);
    expect(chart.width()).toBe(0);
  });

  it('renders a svg @0', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 0,
      data: {
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 100000, "class": "active", "value2": 0, "text": "Text 2"},
          {"value": 100000, "class": "inactive", "value2": 1, "text": "Text 3"},
          {"value": 100000, "class": "active", "value2": 1, "text": "Text 4"},
          {"value": 80000, "class": "inactive", "value2": 0, "text": "Text 1.1"},
          {"value": 60000, "class": "inactive", "value2": 0, "text": "Text 1.2"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 1, "class": "active", "value2": 0, "text": "Text 200000"},
          {"value": 1, "class": "inactive", "value2": 1, "text": "Text 300000"},
          {"value": 1, "class": "active", "value2": 1, "text": "Text 400000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(18*24);
    expect(chart.width()).toBe(0);
  });

  it('renders a svg @100', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 100,
      data: {
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 100000, "class": "active", "value2": 0, "text": "Text 2"},
          {"value": 100000, "class": "inactive", "value2": 1, "text": "Text 3"},
          {"value": 100000, "class": "active", "value2": 1, "text": "Text 4"},
          {"value": 80000, "class": "inactive", "value2": 0, "text": "Text 1.1"},
          {"value": 60000, "class": "inactive", "value2": 0, "text": "Text 1.2"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 1, "class": "active", "value2": 0, "text": "Text 200000"},
          {"value": 1, "class": "inactive", "value2": 1, "text": "Text 300000"},
          {"value": 1, "class": "active", "value2": 1, "text": "Text 400000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(18*24);
    expect(chart.width()).toBe(100);
  });

  it('renders a svg @500', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 500,
      data: {
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 100000, "class": "active", "value2": 0, "text": "Text 2"},
          {"value": 100000, "class": "inactive", "value2": 1, "text": "Text 3"},
          {"value": 100000, "class": "active", "value2": 1, "text": "Text 4"},
          {"value": 80000, "class": "inactive", "value2": 0, "text": "Text 1.1"},
          {"value": 60000, "class": "inactive", "value2": 0, "text": "Text 1.2"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 1, "class": "active", "value2": 0, "text": "Text 200000"},
          {"value": 1, "class": "inactive", "value2": 1, "text": "Text 300000"},
          {"value": 1, "class": "active", "value2": 1, "text": "Text 400000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(18*24);
    expect(chart.width()).toBe(500);
  });

  it('renders a svg @700', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 100000, "class": "active", "value2": 0, "text": "Text 2"},
          {"value": 100000, "class": "inactive", "value2": 1, "text": "Text 3"},
          {"value": 100000, "class": "active", "value2": 1, "text": "Text 4"},
          {"value": 80000, "class": "inactive", "value2": 0, "text": "Text 1.1"},
          {"value": 60000, "class": "inactive", "value2": 0, "text": "Text 1.2"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 1, "class": "active", "value2": 0, "text": "Text 200000"},
          {"value": 1, "class": "inactive", "value2": 1, "text": "Text 300000"},
          {"value": 1, "class": "active", "value2": 1, "text": "Text 400000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(18*24);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg @2000', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 2000,
      data: {
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 100000, "class": "active", "value2": 0, "text": "Text 2"},
          {"value": 100000, "class": "inactive", "value2": 1, "text": "Text 3"},
          {"value": 100000, "class": "active", "value2": 1, "text": "Text 4"},
          {"value": 80000, "class": "inactive", "value2": 0, "text": "Text 1.1"},
          {"value": 60000, "class": "inactive", "value2": 0, "text": "Text 1.2"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 10000, "class": "active", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 1, "class": "active", "value2": 0, "text": "Text 200000"},
          {"value": 1, "class": "inactive", "value2": 1, "text": "Text 300000"},
          {"value": 1, "class": "active", "value2": 1, "text": "Text 400000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(18*24);
    expect(chart.width()).toBe(2000);
  });

  it('renders a svg with majority line @0', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "majority": 0,
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(8*24);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg with majority line @1', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "majority": 1,
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(8*24);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg with majority line @50%', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "majority": 50000,
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(8*24);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg with majority line @100%', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "majority": 100000,
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(8*24);
    expect(chart.width()).toBe(700);
  });

  it('renders a svg with majority line @120%', () => {
    var document = jsdom.jsdom();
    var chart = barChart({
      width: 700,
      data: {
        "majority": 120000,
        "results": [
          {"value": 100000, "class": "inactive", "value2": 0, "text": "Text 1"},
          {"value": 10000, "class": "inactive", "value2": 0, "text": "Text 10"},
          {"value": 10000, "class": "inactive", "value2": 1, "text": "Text 10"},
          {"value": 1000, "class": "inactive", "value2": 0, "text": "Text 100"},
          {"value": 100, "class": "inactive", "value2": 0, "text": "Text 1000"},
          {"value": 10, "class": "inactive", "value2": 0, "text": "Text 10000"},
          {"value": 1, "class": "inactive", "value2": 0, "text": "Text 100000"},
          {"value": 0, "class": "inactive", "value2": 0, "text": "Text 1000000"},
        ]}
    });
    chart(document.body);
    expect(document.svg()).toMatchSnapshot();
    expect(chart.height()).toBe(8*24);
    expect(chart.width()).toBe(700);
  });
});
