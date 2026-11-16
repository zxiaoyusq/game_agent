(function () {
    'use strict';
    try {
        var store = window.localStorage;
        if (store.getItem('CrazyKnifes_Save') === null) {
            var previous = store.getItem('CrazyCutter_Save');
            if (previous !== null) {
                var oldSave = JSON.parse(previous), nextSave = {};
                Object.keys(oldSave).forEach(function (key) {
                    nextSave[key.replace(/^CrazyCutter_Save/, 'CrazyKnifes_Save')] = oldSave[key];
                });
                store.setItem('CrazyKnifes_Save', JSON.stringify(nextSave));
            }
        }
        if (store.getItem('CrazyKnifes_Language') === null) {
            var language = store.getItem('CrazyCutter_Language');
            if (language !== null) store.setItem('CrazyKnifes_Language', language);
        }
    } catch (error) {
        console.error('[Crazy Knifes] Save migration failed', error);
    }
}());
