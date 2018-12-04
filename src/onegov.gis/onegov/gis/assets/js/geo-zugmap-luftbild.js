function spawnDefaultMap(target, options, cb) {
    spawnZugMap(target, options, cb,
        'https://maps.zg.ch/luftbildplus_tiled_lv95',
        'https://maps.zg.ch/ZugMap.API/capabilities/zug_luftbildplus_wmts_2056.xml',
        'LuftbildPlusLV95');
};
