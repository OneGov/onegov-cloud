function spawnDefaultMap(target, options, cb) {
    spawnZugMap(target, options, cb,
        'https://maps.zg.ch/ortsplan_tiled_lv95',
        'https://maps.zg.ch/ZugMap.API/capabilities/zug_ortsplan_wmts_2056.xml',
        'Ortsplan');
};
