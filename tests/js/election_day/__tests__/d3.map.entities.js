const jsdom = require('jsdom');
const path = '../../../../src/onegov/election_day'
const d3 = require(path + '/assets/js/d3');
const topojson = require(path + '/assets/js/topojson');
const mapChart = require(path + '/assets/js/d3.map.entities')(d3, topojson);
const mapdata = require(path + '/static/mapdata/2017/zg.json');
const data = {
  1701: {counted: true, percentage: 60},
  1702: {counted: true, percentage: 60},
  1703: {counted: true, percentage: 60},
  1704: {counted: true, percentage: 60},
  1705: {counted: true, percentage: 60},
  1706: {counted: true, percentage: 60},
  1707: {counted: true, percentage: 60},
  1708: {counted: true, percentage: 60},
  1709: {counted: true, percentage: 60},
  1710: {counted: true, percentage: 60},
  1711: {counted: true, percentage: 60}
};

describe('Map', () => {
  // Note that our bounding box mockup is not good enough to allow the map to
  // find the right height, the viewbox of the generated SVGs is not correct

  it('renders an empty svg with no data', () => {
    var document = jsdom.jsdom();
    var chart = mapChart();
    chart(document.body);
    expect(document.svg(d3)).toMatchSnapshot();
  });

  it('renders an svg of width 1px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 1,
      mapdata: mapdata,
      data: data,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_1px.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(1);
  });

  it('renders an svg of width 200px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 200,
      mapdata: mapdata,
      data: data,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_200px.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(200);
  });

  it('renders an svg of width 500px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 500,
      mapdata: mapdata,
      data: data,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_500px.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(500);
  });

  it('renders an svg of width 700px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: data,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_700px.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders an svg of width 2000px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 2000,
      mapdata: mapdata,
      data: data,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_2000px.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(2000);
  });

  it('renders an svg of width 700px with the red colorscale', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: data,
      canton: 'zg',
      colorScale: 'r'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_700px_red.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders an svg of width 700px with the blue colorscale', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: data,
      canton: 'zg',
      colorScale: 'b'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_700px_blue.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders a partial svg of width 700px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: {
        1701: {counted: true, percentage: 60},
        1702: {counted: true, percentage: 60},
        1703: {counted: false, percentage: 60},
        1704: {counted: false, percentage: 60},
      },
      canton: 'zg',
      colorScale: 'b'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_700px_partial.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders an svg of width 700px with no legend', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: data,
      canton: 'zg',
      hideLegend: true
    });

    chart(document.body);
    require('fs').writeFile("entities_map_700px_no_legend.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders the translations', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 2000,
      mapdata: mapdata,
      data: data,
      canton: 'zg',
      labelLeftHand: 'Nein',
      labelRightHand: 'Ja'
    });

    chart(document.body);
    expect(document.svg()).toMatch('Ja');
    expect(document.svg()).toMatch('Nein');
  });

  // bern
  it('renders a communal svg', () => {
    const communalMapdata = require(path + '/static/mapdata/2017/351.json');
    const communalData = {
      1: {counted: true, percentage: 60},
      2: {counted: true, percentage: 60},
      3: {counted: true, percentage: 60},
      4: {counted: true, percentage: 60},
      5: {counted: true, percentage: 60},
      6: {counted: true, percentage: 60},
    };

    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 500,
      mapdata: communalMapdata,
      data: communalData,
      canton: 'zg'
    });

    chart(document.body);
    require('fs').writeFile("entities_map_500px_communal.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(500);
  });
});
