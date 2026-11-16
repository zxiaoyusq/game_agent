(function () {
    'use strict';

    var STORAGE_KEY = 'CrazyKnifes_Language';
    var DEFAULT_LANGUAGE = 'en';
    var language = DEFAULT_LANGUAGE;
    var panel = null;
    var rawHudState = null;
    var hudWrapped = false;
    var textMirrorRoot = null;
    var textMirrors = [];
    var textMirrorApp = null;
    var lastMirrorScan = 0;
    var textMeasureContext = null;
    var measuredTextWidths = new Map();
    var englishMirrorsRestored = false;
    var mirrorCanvasRect = null;
    var mirrorCanvasRectAt = 0;
    ['resize', 'orientationchange', 'scroll'].forEach(function (eventName) {
        window.addEventListener(eventName, function () { mirrorCanvasRect = null; }, { passive: true, capture: true });
    });
    var mirrorCamera = null;

    var languages = [
        { code: 'en', label: 'ENGLISH' },
        { code: 'pt', label: 'PORTUGUESE' },
        { code: 'fr', label: 'FRENCH' },
        { code: 'sw', label: 'SWAHILI' },
        { code: 'hi', label: 'HINDI' },
        { code: 'bn', label: 'BENGALI' }
    ];

    var copy = {
        en: {
            appName: 'Crazy Knifes',
            settings: 'SETTINGS', language: 'LANGUAGE', selectLanguage: 'SELECT LANGUAGE', tutorial: 'TUTORIAL',
            level: 'LEVEL {n}', bonus: 'BONUS', bonusLevel: 'BONUS LEVEL',
            bonusReady: 'BONUS READY', bonusIn: 'BONUS IN {n}', goalComplete: 'GOAL COMPLETE',
            goalPrefix: 'GOAL: {goal}', complete: 'COMPLETE', go: 'GO!', maxReward: 'MAX REWARD',
            finishTutorial: 'FINISH THE TUTORIAL', sliceObjects: 'SLICE {n} OBJECTS',
            makeCombo: 'MAKE A {n} COMBO', goalCoins: 'GOAL COMPLETE +{n} COINS', close: 'CLOSE',
            pause: 'PAUSE', howToPlay: 'HOW TO PLAY', shop: 'SHOP', unlockRandom: 'UNLOCK\nRANDOM',
            tapToRotate: 'TAP TO\nROTATE', moneyEarned: 'MONEY EARNED', bewareSpikes: 'BEWARE OF SPIKES!',
            score: 'SCORE', levelCompleted: 'LEVEL {n} COMPLETED!', tutorialCompleted: 'TUTORIAL COMPLETED!',
            result: 'RESULT', gameOver: 'GAME OVER', tapToStart: 'TAP TO START',
            keepTappingFly: 'KEEP TAPPING\nTO FLY', tapAnywhereJumpFlip: 'TAP ANYWHERE\nTO JUMP AND FLIP!',
            continueQuestion: 'CONTINUE?', yes: 'YES', noThankYou: 'NO THANK YOU', claimX3: 'CLAIM X 3', claim: 'CLAIM',
            knifeCollectionComplete: 'KNIFE COLLECTION COMPLETE!', newBladesSoon: 'NEW BLADES ARRIVING SOON!',
            noBonus: 'NO BONUS', dontTouchGround: "DON'T TOUCH THE GROUND", bonusBang: 'BONUS!',
            demo: 'DEMO', getFullGame: 'GET FULL GAME', purchaseFullVersion: 'Purchase the full version at'
        },
        pt: {
            appName: 'Crazy Knifes',
            settings: 'CONFIGURAÇÕES', language: 'IDIOMA', selectLanguage: 'SELECIONAR IDIOMA', tutorial: 'TUTORIAL',
            level: 'NÍVEL {n}', bonus: 'BÔNUS', bonusLevel: 'NÍVEL BÔNUS',
            bonusReady: 'BÔNUS PRONTO', bonusIn: 'BÔNUS EM {n}', goalComplete: 'OBJETIVO CONCLUÍDO',
            goalPrefix: 'OBJETIVO: {goal}', complete: 'CONCLUÍDO', go: 'VÁ!', maxReward: 'RECOMPENSA MÁXIMA',
            finishTutorial: 'TERMINE O TUTORIAL', sliceObjects: 'CORTE {n} OBJETOS',
            makeCombo: 'FAÇA UM COMBO DE {n}', goalCoins: 'OBJETIVO CONCLUÍDO +{n} MOEDAS', close: 'FECHAR',
            pause: 'PAUSA', howToPlay: 'COMO JOGAR', shop: 'LOJA', unlockRandom: 'DESBLOQUEAR\nALEATÓRIO',
            tapToRotate: 'TOQUE PARA\nGIRAR', moneyEarned: 'DINHEIRO GANHO', bewareSpikes: 'CUIDADO COM OS ESPINHOS!',
            score: 'PONTUAÇÃO', levelCompleted: 'NÍVEL {n} CONCLUÍDO!', tutorialCompleted: 'TUTORIAL CONCLUÍDO!',
            result: 'RESULTADO', gameOver: 'FIM DE JOGO', tapToStart: 'TOQUE PARA COMEÇAR',
            keepTappingFly: 'CONTINUE TOCANDO\nPARA VOAR', tapAnywhereJumpFlip: 'TOQUE EM QUALQUER LUGAR\nPARA PULAR E GIRAR!',
            continueQuestion: 'CONTINUAR?', yes: 'SIM', noThankYou: 'NÃO, OBRIGADO', claimX3: 'RECEBER X 3', claim: 'RECEBER',
            knifeCollectionComplete: 'COLEÇÃO DE FACAS COMPLETA!', newBladesSoon: 'NOVAS LÂMINAS EM BREVE!',
            noBonus: 'SEM BÔNUS', dontTouchGround: 'NÃO TOQUE NO CHÃO', bonusBang: 'BÔNUS!',
            demo: 'DEMONSTRAÇÃO', getFullGame: 'OBTER JOGO COMPLETO', purchaseFullVersion: 'Compre a versão completa em'
        },
        fr: {
            appName: 'Crazy Knifes',
            settings: 'PARAMÈTRES', language: 'LANGUE', selectLanguage: 'CHOISIR LA LANGUE', tutorial: 'TUTORIEL',
            level: 'NIVEAU {n}', bonus: 'BONUS', bonusLevel: 'NIVEAU BONUS',
            bonusReady: 'BONUS PRÊT', bonusIn: 'BONUS DANS {n}', goalComplete: 'OBJECTIF ATTEINT',
            goalPrefix: 'OBJECTIF : {goal}', complete: 'TERMINÉ', go: 'JOUEZ !', maxReward: 'RÉCOMPENSE MAXIMALE',
            finishTutorial: 'TERMINEZ LE TUTORIEL', sliceObjects: 'COUPEZ {n} OBJETS',
            makeCombo: 'FAITES UN COMBO DE {n}', goalCoins: 'OBJECTIF ATTEINT +{n} PIÈCES', close: 'FERMER',
            pause: 'PAUSE', howToPlay: 'COMMENT JOUER', shop: 'BOUTIQUE', unlockRandom: 'DÉBLOQUER\nAU HASARD',
            tapToRotate: 'TOUCHEZ POUR\nTOURNER', moneyEarned: 'ARGENT GAGNÉ', bewareSpikes: 'ATTENTION AUX PIQUES !',
            score: 'SCORE', levelCompleted: 'NIVEAU {n} TERMINÉ !', tutorialCompleted: 'TUTORIEL TERMINÉ !',
            result: 'RÉSULTAT', gameOver: 'PARTIE TERMINÉE', tapToStart: 'TOUCHEZ POUR COMMENCER',
            keepTappingFly: 'CONTINUEZ À TOUCHER\nPOUR VOLER', tapAnywhereJumpFlip: 'TOUCHEZ N’IMPORTE OÙ\nPOUR SAUTER ET TOURNER !',
            continueQuestion: 'CONTINUER ?', yes: 'OUI', noThankYou: 'NON MERCI', claimX3: 'RÉCUPÉRER X 3', claim: 'RÉCUPÉRER',
            knifeCollectionComplete: 'COLLECTION DE COUTEAUX COMPLÈTE !', newBladesSoon: 'NOUVELLES LAMES BIENTÔT !',
            noBonus: 'AUCUN BONUS', dontTouchGround: 'NE TOUCHEZ PAS LE SOL', bonusBang: 'BONUS !',
            demo: 'DÉMO', getFullGame: 'OBTENIR LE JEU COMPLET', purchaseFullVersion: 'Achetez la version complète sur'
        },
        sw: {
            appName: 'Crazy Knifes',
            settings: 'MIPANGILIO', language: 'LUGHA', selectLanguage: 'CHAGUA LUGHA', tutorial: 'MAFUNZO',
            level: 'KIWANGO {n}', bonus: 'BONASI', bonusLevel: 'KIWANGO CHA BONASI',
            bonusReady: 'BONASI TAYARI', bonusIn: 'BONASI BAADA YA {n}', goalComplete: 'LENGO LIMEKAMILIKA',
            goalPrefix: 'LENGO: {goal}', complete: 'IMEKAMILIKA', go: 'ENDELEA!', maxReward: 'ZAWADI KAMILI',
            finishTutorial: 'MALIZA MAFUNZO', sliceObjects: 'KATA VITU {n}',
            makeCombo: 'FANYA KOMBO YA {n}', goalCoins: 'LENGO LIMEKAMILIKA +SARAFU {n}', close: 'FUNGA',
            pause: 'SIMAMISHA', howToPlay: 'JINSI YA KUCHEZA', shop: 'DUKA', unlockRandom: 'FUNGUA\nBILA MPANGILIO',
            tapToRotate: 'GUSA ILI\nUZUNGUSHE', moneyEarned: 'PESA ULIZOPATA', bewareSpikes: 'JIHADHARI NA MIIBA!',
            score: 'ALAMA', levelCompleted: 'KIWANGO {n} KIMEKAMILIKA!', tutorialCompleted: 'MAFUNZO YAMEKAMILIKA!',
            result: 'MATOKEO', gameOver: 'MCHEZO UMEKWISHA', tapToStart: 'GUSA ILI UANZE',
            keepTappingFly: 'ENDELEA KUGUSA\nILI URUKE', tapAnywhereJumpFlip: 'GUSA POPOTE\nILI URUKE NA UJIZUNGUSHE!',
            continueQuestion: 'UENDELEE?', yes: 'NDIYO', noThankYou: 'HAPANA, ASANTE', claimX3: 'CHUKUA X 3', claim: 'CHUKUA',
            knifeCollectionComplete: 'MKUSANYIKO WA VISU UMEKAMILIKA!', newBladesSoon: 'VISU VIPYA VINAKUJA HIVI KARIBUNI!',
            noBonus: 'HAKUNA BONASI', dontTouchGround: 'USIGUSE ARDHI', bonusBang: 'BONASI!',
            demo: 'JARIBIO', getFullGame: 'PATA MCHEZO KAMILI', purchaseFullVersion: 'Nunua toleo kamili kupitia'
        },
        hi: {
            appName: 'Crazy Knifes',
            settings: 'सेटिंग्स', language: 'भाषा', selectLanguage: 'भाषा चुनें', tutorial: 'प्रशिक्षण',
            level: 'स्तर {n}', bonus: 'बोनस', bonusLevel: 'बोनस स्तर',
            bonusReady: 'बोनस तैयार', bonusIn: '{n} में बोनस', goalComplete: 'लक्ष्य पूरा',
            goalPrefix: 'लक्ष्य: {goal}', complete: 'पूरा', go: 'शुरू!', maxReward: 'अधिकतम इनाम',
            finishTutorial: 'प्रशिक्षण पूरा करें', sliceObjects: '{n} वस्तुएँ काटें',
            makeCombo: '{n} कॉम्बो करें', goalCoins: 'लक्ष्य पूरा +{n} सिक्के', close: 'बंद करें',
            pause: 'रोकें', howToPlay: 'कैसे खेलें', shop: 'दुकान', unlockRandom: 'कोई एक\nअनलॉक करें',
            tapToRotate: 'घुमाने के लिए\nटैप करें', moneyEarned: 'कमाए गए पैसे', bewareSpikes: 'काँटों से बचें!',
            score: 'स्कोर', levelCompleted: 'स्तर {n} पूरा!', tutorialCompleted: 'प्रशिक्षण पूरा!',
            result: 'परिणाम', gameOver: 'खेल समाप्त', tapToStart: 'शुरू करने के लिए टैप करें',
            keepTappingFly: 'उड़ने के लिए\nटैप करते रहें', tapAnywhereJumpFlip: 'कूदने और पलटने के लिए\nकहीं भी टैप करें!',
            continueQuestion: 'जारी रखें?', yes: 'हाँ', noThankYou: 'नहीं, धन्यवाद', claimX3: '3 गुना लें', claim: 'प्राप्त करें',
            knifeCollectionComplete: 'चाकुओं का संग्रह पूरा!', newBladesSoon: 'नई ब्लेड जल्द आ रही हैं!',
            noBonus: 'कोई बोनस नहीं', dontTouchGround: 'ज़मीन को न छुएँ', bonusBang: 'बोनस!',
            demo: 'डेमो', getFullGame: 'पूरा गेम पाएँ', purchaseFullVersion: 'पूरा संस्करण यहाँ खरीदें'
        },
        bn: {
            appName: 'Crazy Knifes',
            settings: 'সেটিংস', language: 'ভাষা', selectLanguage: 'ভাষা বেছে নিন', tutorial: 'প্রশিক্ষণ',
            level: 'স্তর {n}', bonus: 'বোনাস', bonusLevel: 'বোনাস স্তর',
            bonusReady: 'বোনাস প্রস্তুত', bonusIn: '{n} পরে বোনাস', goalComplete: 'লক্ষ্য পূর্ণ',
            goalPrefix: 'লক্ষ্য: {goal}', complete: 'সম্পূর্ণ', go: 'শুরু!', maxReward: 'সর্বোচ্চ পুরস্কার',
            finishTutorial: 'প্রশিক্ষণ শেষ করুন', sliceObjects: '{n}টি বস্তু কাটুন',
            makeCombo: '{n} কম্বো করুন', goalCoins: 'লক্ষ্য পূর্ণ +{n} কয়েন', close: 'বন্ধ করুন',
            pause: 'বিরতি', howToPlay: 'কীভাবে খেলবেন', shop: 'দোকান', unlockRandom: 'যেকোনো একটি\nআনলক করুন',
            tapToRotate: 'ঘোরাতে\nট্যাপ করুন', moneyEarned: 'অর্জিত অর্থ', bewareSpikes: 'কাঁটা থেকে সাবধান!',
            score: 'স্কোর', levelCompleted: 'স্তর {n} সম্পূর্ণ!', tutorialCompleted: 'প্রশিক্ষণ সম্পূর্ণ!',
            result: 'ফলাফল', gameOver: 'খেলা শেষ', tapToStart: 'শুরু করতে ট্যাপ করুন',
            keepTappingFly: 'উড়তে\nট্যাপ করতে থাকুন', tapAnywhereJumpFlip: 'লাফিয়ে ঘুরতে\nযেকোনো জায়গায় ট্যাপ করুন!',
            continueQuestion: 'চালিয়ে যাবেন?', yes: 'হ্যাঁ', noThankYou: 'না, ধন্যবাদ', claimX3: '৩ গুণ নিন', claim: 'নিন',
            knifeCollectionComplete: 'ছুরির সংগ্রহ সম্পূর্ণ!', newBladesSoon: 'নতুন ব্লেড শীঘ্রই আসছে!',
            noBonus: 'কোনো বোনাস নেই', dontTouchGround: 'মাটি ছোঁবেন না', bonusBang: 'বোনাস!',
            demo: 'ডেমো', getFullGame: 'সম্পূর্ণ গেম নিন', purchaseFullVersion: 'সম্পূর্ণ সংস্করণ কিনুন'
        }
    };

    function validLanguage(value) {
        return Object.prototype.hasOwnProperty.call(copy, value);
    }

    function readLanguage() {
        try {
            var queryLanguage = new URLSearchParams(window.location.search).get('lang');
            if (validLanguage(queryLanguage)) return queryLanguage;
        } catch (queryError) {
            // Old WebViews can omit URLSearchParams; persisted settings still work.
        }
        try {
            var stored = window.localStorage.getItem(STORAGE_KEY);
            if (validLanguage(stored)) return stored;
        } catch (error) {
            console.warn('[Crazy Knifes i18n] Could not read language preference', error);
        }
        return DEFAULT_LANGUAGE;
    }

    function template(value, params) {
        params = params || {};
        return value.replace(/\{(\w+)\}/g, function (_, key) {
            return Object.prototype.hasOwnProperty.call(params, key) ? String(params[key]) : '';
        });
    }

    function t(key, params) {
        var dictionary = copy[language] || copy.en;
        return template(dictionary[key] || copy.en[key] || key, params);
    }

    function getLanguageName(code) {
        for (var index = 0; index < languages.length; index++) {
            if (languages[index].code === code) return languages[index].label;
        }
        return languages[0].label;
    }

    function translateGoal(value) {
        var match;
        if (value === 'FINISH THE TUTORIAL') return t('finishTutorial');
        match = /^SLICE (\d+) OBJECTS$/.exec(value);
        if (match) return t('sliceObjects', { n: match[1] });
        match = /^MAKE A (\d+) COMBO$/.exec(value);
        if (match) return t('makeCombo', { n: match[1] });
        return value;
    }

    function translateUiText(value) {
        if (language === DEFAULT_LANGUAGE || typeof value !== 'string') return value;
        var match;
        var normalized = value.replace(/\r\n/g, '\n').trim();
        var exact = {
            'SETTINGS': 'settings', 'PAUSE': 'pause', 'HOW TO PLAY': 'howToPlay', 'SHOP': 'shop',
            'UNLOCK\nRANDOM': 'unlockRandom', 'TAP TO\nROTATE': 'tapToRotate', 'MONEY EARNED': 'moneyEarned',
            'BEWARE OF SPIKES!': 'bewareSpikes', 'BEWARE OF SPIKES': 'bewareSpikes', 'SCORE': 'score',
            'BONUS': 'bonus', 'BONUS!': 'bonusBang', 'BONUS\nLEVEL': 'bonusLevel', 'BONUS\nLEVEL!': 'bonusLevel',
            'RESULT': 'result', 'GAME OVER': 'gameOver', 'TAP TO START': 'tapToStart',
            'KEEP TAPPING\nTO FLY': 'keepTappingFly', 'TAP ANYWHERE\nTO JUMP AND FLIP!': 'tapAnywhereJumpFlip',
            'CONTINUE?': 'continueQuestion', 'YES': 'yes', 'NO THANK YOU': 'noThankYou',
            'CLAIM X 3': 'claimX3', 'CLAIM': 'claim', 'NO BONUS': 'noBonus',
            "DON'T TOUCH THE GROUND": 'dontTouchGround', 'TUTORIAL COMPLETED!': 'tutorialCompleted',
            'KNIFE COLLECTION COMPLETE!\n\nNEW BLADES ARRIVING SOON!': 'knifeCollectionComplete',
            'DEMO': 'demo', 'GET FULL GAME': 'getFullGame', 'Purchase the full version at': 'purchaseFullVersion',
            'TUTORIAL': 'tutorial', 'BONUS READY': 'bonusReady', 'GOAL COMPLETE': 'goalComplete',
            'COMPLETE': 'complete', 'GO!': 'go', 'MAX REWARD': 'maxReward'
        };
        if (exact[normalized]) {
            if (normalized === 'KNIFE COLLECTION COMPLETE!\n\nNEW BLADES ARRIVING SOON!') {
                return t('knifeCollectionComplete') + '\n\n' + t('newBladesSoon');
            }
            return t(exact[normalized]);
        }
        match = /^LEVEL\s+(\d+)\s+COMPLETED!$/i.exec(normalized);
        if (match) return t('levelCompleted', { n: match[1] });
        match = /^LEVEL\s+(\d+)$/i.exec(normalized);
        if (match) return t('level', { n: match[1] });
        match = /^BONUS IN (\d+)$/.exec(normalized);
        if (match) return t('bonusIn', { n: match[1] });
        match = /^GOAL: (.+)$/.exec(normalized);
        if (match) return t('goalPrefix', { goal: translateGoal(match[1]) });
        match = /^GOAL COMPLETE\s*\+(\d+) COINS$/.exec(normalized);
        if (match) return t('goalCoins', { n: match[1] });
        return translateGoal(normalized);
    }

    function translateHudState(state) {
        var translated = {};
        Object.keys(state || {}).forEach(function (key) { translated[key] = state[key]; });
        ['levelLabel', 'bonus', 'goal', 'progressLabel'].forEach(function (key) {
            translated[key] = translateUiText(translated[key]);
        });
        return translated;
    }

    function injectStyles() {
        if (document.getElementById('cc-i18n-style')) return;
        var style = document.createElement('style');
        style.id = 'cc-i18n-style';
        style.textContent = [
            '#cc-language-panel{position:fixed;left:50%;top:calc(50% + clamp(82px,13vh,122px));transform:translate(-50%,-50%);z-index:10000001;width:min(332px,78vw);font-family:system-ui,-apple-system,"Noto Sans","Noto Sans Devanagari","Noto Sans Bengali",sans-serif;color:#fff;text-align:center;pointer-events:auto;touch-action:manipulation;filter:drop-shadow(0 3px 5px rgba(0,0,0,.32))}',
            '#cc-language-panel[hidden]{display:none!important}',
            '#cc-language-panel .cc-language-caption{margin:0 0 5px;color:#314c73;font-size:clamp(11px,2.8vw,14px);font-weight:950;letter-spacing:.8px;text-shadow:0 1px 0 rgba(255,255,255,.9)}',
            '#cc-language-current{box-sizing:border-box;width:100%;min-height:43px;padding:8px 36px 8px 14px;border:2px solid rgba(255,255,255,.9);border-radius:13px;background:linear-gradient(180deg,rgba(47,94,133,.96),rgba(20,49,76,.96));color:#fff;font:900 clamp(13px,3.4vw,17px)/1.1 system-ui,-apple-system,"Noto Sans","Noto Sans Devanagari","Noto Sans Bengali",sans-serif;letter-spacing:.4px;position:relative}',
            '#cc-language-current:after{content:"▾";position:absolute;right:14px;top:50%;transform:translateY(-52%);font-size:18px;color:#62e8ff}',
            '#cc-language-menu{position:fixed;inset:0;z-index:10000002;display:flex;align-items:center;justify-content:center;padding:max(18px,env(safe-area-inset-top)) 16px max(18px,env(safe-area-inset-bottom));background:rgba(5,14,24,.74);pointer-events:auto}',
            '#cc-language-menu[hidden]{display:none!important}',
            '#cc-language-menu .cc-language-card{box-sizing:border-box;width:min(430px,90vw);padding:18px;border:2px solid rgba(255,255,255,.9);border-radius:20px;background:linear-gradient(180deg,rgba(35,76,111,.98),rgba(12,34,55,.98));box-shadow:0 14px 40px rgba(0,0,0,.42)}',
            '#cc-language-menu h2{margin:0 0 14px;font:900 clamp(18px,5vw,25px)/1.15 system-ui,-apple-system,"Noto Sans","Noto Sans Devanagari","Noto Sans Bengali",sans-serif}',
            '#cc-language-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}',
            '#cc-language-options button,#cc-language-close{box-sizing:border-box;min-height:46px;border:1px solid rgba(255,255,255,.72);border-radius:12px;background:rgba(255,255,255,.12);color:#fff;font:850 clamp(11px,3vw,15px)/1.05 system-ui,-apple-system,"Noto Sans","Noto Sans Devanagari","Noto Sans Bengali",sans-serif;letter-spacing:.15px;padding:8px 6px}',
            '#cc-language-options button[aria-pressed="true"]{border-color:#fff45d;background:rgba(255,244,93,.22);box-shadow:0 0 0 2px rgba(255,244,93,.18) inset}',
            '#cc-language-close{width:100%;margin-top:12px;background:rgba(98,232,255,.22);border-color:#62e8ff}',
            '#cc-language-options button:active,#cc-language-close:active,#cc-language-current:active{transform:scale(.98)}',
            '#cc-game-text-mirrors{position:fixed;inset:0;z-index:9999990;overflow:hidden;pointer-events:none;contain:layout style paint}',
            '.cc-game-text-mirror{position:fixed;box-sizing:border-box;display:flex;white-space:pre;overflow:hidden;font-family:"Arial Black","Nirmala UI","Noto Sans Devanagari","Noto Sans Bengali",system-ui,sans-serif;font-weight:900;line-height:1;text-rendering:geometricPrecision;pointer-events:none;text-shadow:0 1px 2px rgba(0,0,0,.52);transform-origin:center center}',
            '.cc-game-text-mirror[hidden]{display:none!important}',
            '@media(max-height:590px){#cc-language-panel{top:calc(50% + 80px)}#cc-language-menu .cc-language-card{padding:13px}#cc-language-options button{min-height:39px}#cc-language-menu h2{margin-bottom:9px}}'
        ].join('');
        document.head.appendChild(style);
    }

    function stopGameInput(event) {
        event.stopPropagation();
    }

    function ensurePanel() {
        if (panel && panel.isConnected) return panel;
        if (!document.body) return null;
        injectStyles();

        panel = document.createElement('div');
        panel.id = 'cc-language-panel';
        panel.hidden = true;
        panel.innerHTML = '<div class="cc-language-caption"></div><button id="cc-language-current" type="button" aria-haspopup="dialog" aria-expanded="false"></button>';

        var menu = document.createElement('div');
        menu.id = 'cc-language-menu';
        menu.hidden = true;
        menu.setAttribute('role', 'dialog');
        menu.setAttribute('aria-modal', 'true');
        menu.innerHTML = '<div class="cc-language-card"><h2></h2><div id="cc-language-options"></div><button id="cc-language-close" type="button"></button></div>';
        var options = menu.querySelector('#cc-language-options');
        languages.forEach(function (item) {
            var button = document.createElement('button');
            button.type = 'button';
            button.dataset.language = item.code;
            button.textContent = item.label;
            options.appendChild(button);
        });

        ['pointerdown', 'mousedown', 'touchstart', 'click'].forEach(function (eventName) {
            panel.addEventListener(eventName, stopGameInput, { passive: true });
            menu.addEventListener(eventName, stopGameInput, { passive: true });
        });
        panel.querySelector('#cc-language-current').addEventListener('click', function () {
            menu.hidden = false;
            this.setAttribute('aria-expanded', 'true');
        });
        menu.querySelector('#cc-language-close').addEventListener('click', function () {
            closeMenu();
        });
        menu.addEventListener('click', function (event) {
            var button = event.target.closest('[data-language]');
            if (!button) return;
            setLanguage(button.dataset.language);
            closeMenu();
        });

        document.body.appendChild(panel);
        document.body.appendChild(menu);
        updatePanelCopy();
        return panel;
    }

    function closeMenu() {
        var menu = document.getElementById('cc-language-menu');
        if (menu) menu.hidden = true;
        var current = document.getElementById('cc-language-current');
        if (current) current.setAttribute('aria-expanded', 'false');
    }

    function updatePanelCopy() {
        if (!panel) return;
        panel.querySelector('.cc-language-caption').textContent = t('language');
        panel.querySelector('#cc-language-current').textContent = getLanguageName(language);
        var menu = document.getElementById('cc-language-menu');
        if (!menu) return;
        menu.querySelector('h2').textContent = t('selectLanguage');
        menu.querySelector('#cc-language-close').textContent = t('close');
        var buttons = menu.querySelectorAll('[data-language]');
        for (var index = 0; index < buttons.length; index++) {
            buttons[index].setAttribute('aria-pressed', buttons[index].dataset.language === language ? 'true' : 'false');
        }
    }

    function settingsVisible() {
        try {
            return Boolean(window.Uipopup && typeof window.Uipopup.isShown === 'function' && window.Uipopup.isShown('Settings'));
        } catch (error) {
            return false;
        }
    }

    function syncPanelVisibility() {
        var target = ensurePanel();
        if (!target) return;
        var visible = settingsVisible();
        if (target.hidden === visible) target.hidden = !visible;
        var menu = document.getElementById('cc-language-menu');
        if (!visible && menu && !menu.hidden) closeMenu();
    }

    function wrapEngagementHud() {
        if (hudWrapped || !window.CrazyKnifesEngagementHUD || typeof window.CrazyKnifesEngagementHUD.set !== 'function') return;
        hudWrapped = true;
        var originalSet = window.CrazyKnifesEngagementHUD.set;
        var originalToast = window.CrazyKnifesEngagementHUD.toast;
        window.CrazyKnifesEngagementHUD.set = function (state) {
            rawHudState = state;
            return originalSet.call(window.CrazyKnifesEngagementHUD, translateHudState(state));
        };
        window.CrazyKnifesEngagementHUD.toast = function (message) {
            return originalToast.call(window.CrazyKnifesEngagementHUD, translateUiText(message));
        };
    }

    function gameApp() {
        try {
            if (window.pc && pc.AppBase && typeof pc.AppBase.getApplication === 'function') {
                return pc.AppBase.getApplication();
            }
            if (window.pc && pc.Application && typeof pc.Application.getApplication === 'function') {
                return pc.Application.getApplication();
            }
        } catch (error) {
            return null;
        }
        return null;
    }

    function entityPath(entity) {
        var result = [];
        var current = entity;
        var guard = 0;
        while (current && guard < 40) {
            result.push(current.name || 'Entity');
            current = current.parent;
            guard += 1;
        }
        return result.reverse().join('/');
    }

    function enabledInHierarchy(entity) {
        var current = entity;
        var guard = 0;
        while (current && guard < 40) {
            if (current.enabled === false || current.enabledInHierarchy === false || current._enabledInHierarchy === false) return false;
            current = current.parent;
            guard += 1;
        }
        return true;
    }

    function ensureTextMirrorRoot() {
        if (textMirrorRoot && textMirrorRoot.isConnected) return textMirrorRoot;
        if (!document.body) return null;
        injectStyles();
        textMirrorRoot = document.createElement('div');
        textMirrorRoot.id = 'cc-game-text-mirrors';
        textMirrorRoot.setAttribute('aria-hidden', 'true');
        document.body.appendChild(textMirrorRoot);
        return textMirrorRoot;
    }

    function scanGameTextComponents(force) {
        var now = Date.now();
        if (!force && now - lastMirrorScan < 2000) return;
        lastMirrorScan = now;
        var app = gameApp();
        var root = ensureTextMirrorRoot();
        if (!app || !app.root || !root || typeof app.root.findComponents !== 'function') return;
        if (textMirrorApp !== app) {
            textMirrorApp = app;
            textMirrors.forEach(function (record) { record.node.remove(); });
            textMirrors = [];
        }
        textMirrors = textMirrors.filter(function (record) {
            if (record.entity && record.entity.element === record.component && record.entity.parent) return true;
            record.node.remove();
            return false;
        });
        var known = new Set(textMirrors.map(function (record) { return record.component; }));
        var components = app.root.findComponents('element') || [];
        components.forEach(function (component) {
            if (!component || component.type !== 'text' || known.has(component)) return;
            var node = document.createElement('div');
            node.className = 'cc-game-text-mirror';
            node.hidden = true;
            root.appendChild(node);
            textMirrors.push({
                component: component,
                entity: component.entity,
                path: entityPath(component.entity),
                node: node,
                hiddenOriginal: false,
                meshVisibility: []
            });
        });
    }

    function activeModalPath(app) {
        var popupNames = [
            ['Settings', '/SettingsPopup/'],
            ['Pause', '/PausePopup/'],
            ['Tutor', '/TutorPopup/']
        ];
        try {
            for (var index = 0; index < popupNames.length; index++) {
                if (window.Uipopup && Uipopup.isShown(popupNames[index][0])) return popupNames[index][1];
            }
        } catch (error) {
            // Popup state is optional during the first frames.
        }
        return '';
    }

    function restoreGameText(record) {
        if (record.hiddenOriginal) {
            record.meshVisibility.forEach(function (entry) {
                entry.mesh.visible = entry.visible;
            });
            record.meshVisibility = [];
            record.hiddenOriginal = false;
        }
        if (!record.node.hidden) record.node.hidden = true;
    }

    function hideOriginalGameText(record) {
        var textRenderer = record.component._text;
        var model = textRenderer && textRenderer._model;
        var meshes = model && model.meshInstances ? model.meshInstances : [];
        if (!record.hiddenOriginal) {
            record.meshVisibility = [];
            for (var index = 0; index < meshes.length; index++) {
                record.meshVisibility.push({ mesh: meshes[index], visible: meshes[index].visible });
            }
            record.hiddenOriginal = true;
        }
        for (var meshIndex = 0; meshIndex < meshes.length; meshIndex++) meshes[meshIndex].visible = false;
    }

    function colorChannel(value) {
        return Math.max(0, Math.min(255, Math.round((Number(value) || 0) * 255)));
    }

    function screenForEntity(entity) {
        var current = entity;
        var guard = 0;
        while (current && guard < 40) {
            if (current.screen) return current.screen;
            current = current.parent;
            guard += 1;
        }
        return null;
    }

    function projectedCorners(component, app) {
        var screen = screenForEntity(component.entity);
        if (!screen || screen.screenSpace !== false) return { corners: component.screenCorners, topOrigin: false };
        var worldCorners = component.worldCorners;
        var owner = window.CameraController && CameraController.instance;
        var camera = owner && owner.entity.camera;
        if (!camera) camera = mirrorCamera;
        if (!camera || !camera.enabled || !enabledInHierarchy(camera.entity)) {
            var cameras = app.root.findComponents('camera') || [];
            camera = cameras.find(function (value) { return value.enabled && enabledInHierarchy(value.entity); });
        }
        mirrorCamera = camera;
        if (!camera || !worldCorners || !worldCorners.length) return null;
        return {
            corners: worldCorners.map(function (corner) {
                // CameraComponent.worldToScreen reads clientRect twice per
                // corner. Reuse this frame's CSS dimensions with pc.Camera.
                return camera.camera.worldToScreen(corner, mirrorCanvasRect.width, mirrorCanvasRect.height, new pc.Vec3());
            }),
            topOrigin: true
        };
    }

    function gameHintIsReady(entity) {
        var current = entity;
        var guard = 0;
        while (current && guard < 40) {
            var hint = current.script && current.script.gameHint;
            if (hint && hint.shown !== true) return false;
            current = current.parent;
            guard += 1;
        }
        return true;
    }

    function gameStateAllows(record) {
        try {
            if (record.path.indexOf('/Level1/') !== -1 && window.Game && Game.state !== Game.STATE_PLAYING) return false;
        } catch (error) {
            return true;
        }
        return true;
    }

    function fitFontToBox(text, fontSize, lineHeight, width, height) {
        if (!textMeasureContext) textMeasureContext = document.createElement('canvas').getContext('2d');
        if (!textMeasureContext) return { fontSize: fontSize, lineHeight: lineHeight };
        var key = String(text);
        var measured = measuredTextWidths.get(key);
        if (!measured) {
            textMeasureContext.font = '900 100px "Arial Black", "Nirmala UI", sans-serif';
            var lines = key.split('\n');
            var maxWidth = 1;
            for (var index = 0; index < lines.length; index++) maxWidth = Math.max(maxWidth, textMeasureContext.measureText(lines[index]).width);
            measured = { widthAt100: maxWidth, lines: lines.length };
            if (measuredTextWidths.size >= 256) measuredTextWidths.delete(measuredTextWidths.keys().next().value);
            measuredTextWidths.set(key, measured);
        }
        var maxLineWidth = measured.widthAt100 * fontSize / 100;
        var widthScale = width > 0 ? width * 0.94 / maxLineWidth : 1;
        var heightScale = height > 0 ? height * 0.94 / Math.max(1, measured.lines * lineHeight) : 1;
        var scale = Math.min(1, widthScale, heightScale);
        return { fontSize: Math.max(8, fontSize * scale), lineHeight: Math.max(8, lineHeight * scale) };
    }

    function layoutTextMirror(record, canvas, app, translated, modalPath) {
        var component = record.component;
        var entity = record.entity;
        if (!entity || entity.element !== component) { if (!record.node.hidden) record.node.hidden = true; return; }
        var currentOpacity = Number(component.opacity);
        if (!component.enabled || !enabledInHierarchy(entity) || !gameStateAllows(record) || !gameHintIsReady(entity) || currentOpacity <= 0 || (modalPath && record.path.indexOf(modalPath) === -1)) {
            if (!record.node.hidden) record.node.hidden = true;
            return;
        }
        var projection = projectedCorners(component, app);
        var corners = projection && projection.corners;
        if (!corners || corners.length < 4) {
            if (!record.node.hidden) record.node.hidden = true;
            return;
        }
        var rect = mirrorCanvasRect || canvas.getBoundingClientRect();
        // CameraComponent.worldToScreen uses CSS clientRect dimensions; screen
        // element screenCorners instead use render-buffer pixel dimensions.
        var deviceWidth = projection.topOrigin ? rect.width : app.graphicsDevice.width || canvas.width || rect.width;
        var deviceHeight = projection.topOrigin ? rect.height : app.graphicsDevice.height || canvas.height || rect.height;
        var minX = Infinity;
        var maxX = -Infinity;
        var minY = Infinity;
        var maxY = -Infinity;
        for (var index = 0; index < corners.length; index++) {
            minX = Math.min(minX, corners[index].x);
            maxX = Math.max(maxX, corners[index].x);
            minY = Math.min(minY, corners[index].y);
            maxY = Math.max(maxY, corners[index].y);
        }
        if (!isFinite(minX + maxX + minY + maxY) || maxX <= minX || maxY <= minY) {
            if (!record.node.hidden) record.node.hidden = true;
            return;
        }
        var scaleX = rect.width / deviceWidth;
        var scaleY = rect.height / deviceHeight;
        var cssWidth = (maxX - minX) * scaleX;
        var cssHeight = (maxY - minY) * scaleY;
        var cssLeft = rect.left + minX * scaleX;
        var cssTop = rect.top + (projection.topOrigin ? minY : deviceHeight - maxY) * scaleY;
        if (cssLeft + cssWidth < 0 || cssTop + cssHeight < 0 || cssLeft > innerWidth || cssTop > innerHeight) {
            if (!record.node.hidden) record.node.hidden = true;
            return;
        }
        var baseHeight = Number(component.height || component.calculatedHeight || maxY - minY) || 1;
        var fontSize = Math.max(8, Number(component.fontSize || 24) * cssHeight / baseHeight);
        var lineHeight = Math.max(fontSize, Number(component.lineHeight || component.fontSize || 24) * cssHeight / baseHeight);
        var fitKey = translated + '|' + [fontSize, lineHeight, cssWidth, cssHeight].map(function (value) { return Math.round(value * 4); }).join(',');
        if (record.fitKey !== fitKey) {
            record.fitKey = fitKey;
            record.fittedFont = fitFontToBox(translated, fontSize, lineHeight, cssWidth, cssHeight);
        }
        var fittedFont = record.fittedFont;
        fontSize = fittedFont.fontSize;
        lineHeight = fittedFont.lineHeight;
        var alignment = component.alignment || { x: 0.5, y: 0.5 };
        var alignX = alignment.x !== undefined ? alignment.x : alignment[0];
        var alignY = alignment.y !== undefined ? alignment.y : alignment[1];
        var color = component.color || { r: 1, g: 1, b: 1 };
        var red = color.r !== undefined ? color.r : color[0];
        var green = color.g !== undefined ? color.g : color[1];
        var blue = color.b !== undefined ? color.b : color[2];
        var node = record.node;
        if (node.textContent !== translated) node.textContent = translated;
        var layoutKey = [cssLeft, cssTop, cssWidth, cssHeight, fontSize, lineHeight, currentOpacity, red, green, blue, alignX, alignY].map(function (value) { return Math.round(Number(value) * 100); }).join(',');
        if (record.layoutKey === layoutKey) { if (node.hidden) node.hidden = false; return; }
        record.layoutKey = layoutKey;
        node.style.left = cssLeft + 'px';
        node.style.top = cssTop + 'px';
        node.style.width = cssWidth + 'px';
        node.style.height = cssHeight + 'px';
        node.style.fontSize = fontSize + 'px';
        node.style.lineHeight = lineHeight + 'px';
        node.style.color = 'rgb(' + colorChannel(red) + ',' + colorChannel(green) + ',' + colorChannel(blue) + ')';
        node.style.opacity = String(isFinite(currentOpacity) ? currentOpacity : 1);
        node.style.textAlign = alignX < 0.34 ? 'left' : alignX > 0.66 ? 'right' : 'center';
        node.style.justifyContent = alignX < 0.34 ? 'flex-start' : alignX > 0.66 ? 'flex-end' : 'center';
        node.style.alignItems = alignY < 0.34 ? 'flex-end' : alignY > 0.66 ? 'flex-start' : 'center';
        node.hidden = false;
    }

    function syncGameTextMirrors() {
        if (language === DEFAULT_LANGUAGE) {
            if (!englishMirrorsRestored) textMirrors.forEach(restoreGameText);
            englishMirrorsRestored = true;
            return;
        }
        englishMirrorsRestored = false;
        scanGameTextComponents(false);
        var app = textMirrorApp;
        var canvas = document.getElementById('application-canvas');
        if (!app || !canvas) return;
        var now = Date.now();
        if (!mirrorCanvasRect || now - mirrorCanvasRectAt > 1000) {
            mirrorCanvasRect = canvas.getBoundingClientRect();
            mirrorCanvasRectAt = now;
        }
        var modalPath = activeModalPath(app);
        textMirrors.forEach(function (record) {
            if (!record.entity || record.entity.element !== record.component) { if (!record.node.hidden) record.node.hidden = true; return; }
            var source = record.component.text;
            var translated = translateUiText(source);
            var shouldMirror = language !== DEFAULT_LANGUAGE && typeof source === 'string' && translated !== source;
            if (!shouldMirror) {
                restoreGameText(record);
                return;
            }
            hideOriginalGameText(record);
            layoutTextMirror(record, canvas, app, translated, modalPath);
        });
    }

    function setLanguage(nextLanguage) {
        if (!validLanguage(nextLanguage)) return false;
        language = nextLanguage;
        try {
            window.localStorage.setItem(STORAGE_KEY, language);
        } catch (error) {
            console.warn('[Crazy Knifes i18n] Could not save language preference', error);
        }
        document.documentElement.lang = language;
        document.title = t('appName');
        updatePanelCopy();
        if (rawHudState && window.CrazyKnifesEngagementHUD) {
            window.CrazyKnifesEngagementHUD.set(rawHudState);
        }
        if (language !== DEFAULT_LANGUAGE) scanGameTextComponents(true);
        englishMirrorsRestored = false;
        syncGameTextMirrors();
        window.dispatchEvent(new CustomEvent('crazyknifeslanguagechange', { detail: { language: language } }));
        return true;
    }

    language = readLanguage();
    document.documentElement.lang = language;
        document.title = t('appName');

    window.CrazyKnifesI18n = {
        storageKey: STORAGE_KEY,
        languages: languages.slice(),
        getLanguage: function () { return language; },
        setLanguage: setLanguage,
        t: t,
        translateUiText: translateUiText,
        translateHudState: translateHudState,
        syncGameTextMirrors: syncGameTextMirrors
    };

    wrapEngagementHud();
    window.setInterval(function () {
        wrapEngagementHud();
        syncPanelVisibility();
        syncGameTextMirrors();
    }, 50);
    document.addEventListener('DOMContentLoaded', function () {
        ensurePanel();
        syncPanelVisibility();
    }, { once: true });
}());
