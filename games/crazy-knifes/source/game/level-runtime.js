(function () {
    'use strict';
    var data = null;
    var levels = Object.create(null);
    var requests = Object.create(null);
    var dataOrder = [];
    var templates = Object.create(null);
    var templateOrder = [];
    var loading = null;
    window.CrazyKnifesLevels = {
        load: function (url) {
            if (!loading) loading = fetch(url).then(function (response) {
                if (!response.ok) throw new Error('Level data: HTTP ' + response.status);
                return response.json();
            }).then(function (value) {
                if (!value.levels || Object.keys(value.levels).length !== 42) throw new Error('Incomplete level library');
                data = value;
            });
            return loading;
        },
        has: function (id) { return Boolean(data && data.levels[id]); },
        index: function () { return data; },
        ready: function (id) { return Boolean(levels[id]); },
        ensure: function (ids) {
            return Promise.all(ids.map(function (id) {
                if (!data || !data.levels[id]) return Promise.reject(new Error('Missing level '+id));
                if (levels[id]) return Promise.resolve();
                if (!requests[id]) requests[id] = fetch(data.levels[id].url + '?v=' + window.CC_CACHE_VERSION).then(function(response) {
                    if (!response.ok) throw new Error('Level '+id+': HTTP '+response.status);
                    return response.json();
                }).then(function (value) {
                    if (!value.entities || Object.keys(value.entities).length !== data.levels[id].entities) throw new Error('Incomplete level '+id);
                    levels[id] = value;
                    dataOrder.push(String(id));
                    // Templates and active clones own their independent graph.
                    while (dataOrder.length > 8) delete levels[dataOrder.shift()];
                }).finally(function () { delete requests[id]; });
                return requests[id];
            }));
        },
        instantiate: function (id, app) {
            if (!levels[id]) throw new Error('Level not prepared ' + id);
            if (!templates[id]) templates[id] = new pc.Template(app, {
                entities: levels[id].entities,
                compressedFormat: data.compressedFormat
            });
            var entity = templates[id].instantiate();
            entity.tags.add('level');
            templateOrder = templateOrder.filter(function (value) { return value !== String(id); });
            templateOrder.push(String(id));
            while (templateOrder.length > 4) {
                var expired = templateOrder.shift();
                // The pinned 1.69 engine has no public Template.destroy(). The
                // detached source hierarchy owns its components; clones retain
                // their independent entity/component instances.
                if (templates[expired]._templateRoot) templates[expired]._templateRoot.destroy();
                delete templates[expired];
            }
            return entity;
        },
        loadedTemplateCount: function () { return Object.keys(templates).length; },
        loadedDataCount: function () { return Object.keys(levels).length; }
    };
}());
