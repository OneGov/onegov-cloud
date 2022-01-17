const jsdom = require('jsdom');
const path = '../../../../src/onegov/election_day'
const d3 = require(path + '/assets/js/d3');
const topojson = require(path + '/assets/js/topojson');
const mapChart = require(path + '/assets/js/d3.map.districts')(d3, topojson);
const mapdata = require(path + '/static/mapdata/2017/gr.json');
const data = {
  "Albula": {
    counted: true,
    entities: [3506,3514,3513,3521,3543,3542,3522],
    percentage: 41.8
  },
  "Bernina": {
    counted: true,
    entities: [3561,3551],
    percentage: 47.1
  },
  "Engiadina": {
    counted: true,
    entities: [3752,3847,3746,3764,3762],
    percentage: 39.0
  },
  "Imboden": {
    counted: true,
    entities: [3722,3734,3733,3732,3723,3731,3721],
    percentage: 35.9
  },
  "Landquart": {
    counted: true,
    entities: [3951,3955,3954,3952,3946,3945,3953,3947],
    percentage: 35.8
  },
  "Maloja": {
    counted: true,
    entities: [3786,3787,3789,3792,3788,3783,3781,3790,3785,3784,3791,3782],
    percentage: 48.3
  },
  "Moesa": {
    counted: true,
    entities: [3804,3831,3810,3834,3821,3835,3832,3837,3823,3805,3808,3822],
    percentage: 39.7
  },
  "Plessur": {
    counted: true,
    entities: [3941,3926,3921,3901,3911,3932],
    percentage: 34.8
  },
  "Pr\u00e4ttigau": {
    counted: true,
    entities: [3861,3862,3962,3972,3882,3881,3863,3891,3871,3851,3961],
    percentage: 39.3
  },
  "Surselva": {
    counted: true,
    entities: [3985,3988,3611,3616,3619,3575,3986,3581,3618,3981,3987,3983,3582,3672,3982,3603,3572],
    percentage: 38.1
  },
  "Viamala":{
      counted: true,
      entities: [3695,3638,3708,3670,3633,3662,3503,3712,3668,3705,3703,3691,3711,3707,3694,3681,3663,3713,3673,3637,3669,3640,3661,3701,3693],
      percentage: 32.3096339924274
  }
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
    // require('fs').writeFile("district_map_1px.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_200px.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_500px.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_700px.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_2000px.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_700px_red.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_700px_blue.svg", document.svg(), function(err, result) {});
    expect(document.svg()).toMatchSnapshot();
    expect(chart.width()).toBe(700);
  });

  it('renders a partial svg of width 700px', () => {
    var document = jsdom.jsdom();
    var chart = mapChart({
      width: 700,
      mapdata: mapdata,
      data: {
        "Albula": {
          counted: true,
          entities: [3506,3514,3513,3521,3543,3542,3522],
          percentage: 41.8
        },
        "Bernina": {
          counted: true,
          entities: [3561], // 3551 not included!
          percentage: 47.1
        },
        "Engiadina": {
          counted: false,
          entities: [3752,3847,3746,3764,3762],
          percentage: 39.0
        },
      },
      canton: 'zg',
      colorScale: 'b'
    });

    chart(document.body);
    // require('fs').writeFile("district_map_700px_partial.svg", document.svg(), function(err, result) {});
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
    // require('fs').writeFile("district_map_700px_no_legend.svg", document.svg(), function(err, result) {});
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
});
