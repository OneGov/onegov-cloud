const getMapboxToken = () => document.body.dataset.mapboxToken || false;

console.log('search-js');

document.getElementById('search-js').addEventListener('load', () => {
    console.log('search-js');
  mapboxsearch.config.accessToken = getMapboxToken();
  mapboxsearch.autofill({
    options: {
      country: 'ch'
    }
  });
});
