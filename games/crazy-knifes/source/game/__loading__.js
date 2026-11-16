// Loading & elements

function dj_place(elemName, pivotX, pivotY, deltaX, deltaY, centerPivot) {
	var elemProps = loadingElements[elemName];
	if (!elemProps) return 1;

	if (centerPivot) {
		elemProps.elem.style.left = loadingDisplayParams.width * (pivotX + deltaX / defaultScreenSizePx.width) - parseInt(elemProps.elem.style.width, 10) * 0.5 + "px";
		elemProps.elem.style.top = loadingDisplayParams.height * (pivotY + deltaY / defaultScreenSizePx.height) - parseInt(elemProps.elem.style.height, 10) * 0.5 + "px";
        

	} else {
		elemProps.elem.style.left = loadingDisplayParams.width * (pivotX + deltaX / defaultScreenSizePx.width) + "px";
		elemProps.elem.style.top = loadingDisplayParams.height * (pivotY + deltaY / defaultScreenSizePx.height) + "px";

	}
    if (elemName=='img_loadingbar')
        elemProps.elem.style.top = (loadingDisplayParams.height * (pivotY + deltaY / defaultScreenSizePx.height) - 8 * 0.5).toString() + "px";
        
	elemProps.elem.style.display = "block";
};

function dj_scaleRelative(elemName, sizeOnScreen, scaleByHeight, stretch) {
	var elemProps = loadingElements[elemName];
	if (!elemProps) return;

	if (stretch) {
		elemProps.elem.style.width = sizeOnScreen * loadingDisplayParams.width + "px";
		elemProps.elem.style.height = sizeOnScreen * loadingDisplayParams.height + "px";
	} else {
		var sc = sizeOnScreen * loadingDisplayParams.width / elemProps.width;
		if (scaleByHeight) sc = sizeOnScreen * loadingDisplayParams.height / elemProps.height;

		elemProps.elem.style.width = sc * elemProps.width + "px";
		elemProps.elem.style.height = sc * elemProps.height + "px";
	}

};

function dj_scale(elemName, sizeX, sizeY, stretch) {
	var elemProps = loadingElements[elemName];
	if (!elemProps) return;

	if (stretch) {
		elemProps.elem.style.width = sizeX + "px";
		elemProps.elem.style.height = sizeY + "px";
	} else {
		var sc = sizeX / elemProps.width;

		elemProps.elem.style.width = sc * elemProps.width + "px";
		elemProps.elem.style.height = sc * elemProps.height + "px";
	}

};

var loadingDisplayParams =
{
	width: 100,
	height: 100
};

var defaultScreenSizePx =
{
	width: 1400,
	height: 720
};


//var canvasNode = document.getElementById('canvas');
var loadingElements = {};

var loadingLanguage = 'en';
var runsOnMobileDevice = false;
var loadingHidden = false;





runsOnMobileDevice = dg_mobileAndTabletCheck();



function dg_mobileAndTabletCheck() {
	let check = false;
	(function (a) { if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino|android|ipad|playbook|silk/i.test(a) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0, 4))) check = true; })(navigator.userAgent || navigator.vendor || window.opera);
	return check;
};

function dj_addLoadingElement(elementIdName) {
	var el = document.getElementById(elementIdName);
	var obj = { elem: el, width: el.naturalWidth, height: el.naturalHeight };
	
	el.setAttribute('draggable', false);

	loadingElements[elementIdName] = obj;
	if ((elementIdName != 'img_bgLoading') && (elementIdName != 'img_loadingbaroverlay')) {
	//	el.style.display = "none";
	}

};


function dg_updateElements() {
    if (loadingHidden) return 1;

	var suffix = '';
	//if (loadingLanguage == 'ru') suffix = '_ru';

	//dj_place('img_bgLoading', 0, 0, 0, 0, false);
	//dj_scale('img_bgLoading', 1, 1, true);

	//dj_place('img_pcLogoLoading', 0.5, 0.5, 0, 0, true);
	dj_place('img_loadingbar', 0.5, 1, 0, -120, true);

	if (loadingDisplayParams.width > loadingDisplayParams.height)
	{
		dj_scaleRelative('img_pcLogoLoading' + suffix, 0.25*1, true, false);
        if (loadingElements['img_loadingbar'])
		loadingElements['img_loadingbar'].elem.style.width = loadingDisplayParams.width * 0.5 + "px";

	} else
	{
		dj_scaleRelative('img_pcLogoLoading' + suffix, 0.18*1, true, false);
        if (loadingElements['img_loadingbar'])
		loadingElements['img_loadingbar'].elem.style.width = loadingDisplayParams.width * 0.6 + "px";
		}

}

var loadingProgress = 0;
var loadingAnimated = false;
var animateInterval = null;

var subButtonInitialized = false;
var subButtonEnabled = false;

function dj_loading(value) {
	if (loadingHidden) return 1;

	loadingDisplayParams.width = window.innerWidth;
	loadingDisplayParams.height = window.innerHeight;
	
	dg_updateElements();
	loadingProgress = value;

//if (loadingElements['img_loadingbaroverlay'])
//	loadingElements['img_loadingbaroverlay'].elem.style.width = (value * 100) + "%";
if (loadingElements['img_loadingbar'])
	loadingElements['img_loadingbar'].elem.style.opacity = "1.0";
}


function dg_hideElement(elem) {
	if (elem) {
		elem.style.display = "none";
		elem.style.visibility = "hidden";
		elem.style.pointerEvents = 'none';
		if (elem.parentNode)
			elem.parentNode.removeChild(elem);
	}
}

function dg_hideElementByName(elemName) {
	var elem = loadingElements[elemName];
	if (elem) elem = elem.elem;
	dg_hideElement(elem);
}

function dg_hide_loading_pls() {
	loadingHidden = true;
	for (var key in loadingElements) {
		if (loadingElements.hasOwnProperty(key)) {
			//console.log(key + " -> " + loadingElements[key]);
			dg_hideElement(loadingElements[key].elem);
		}
	}
    
    var splash = document.getElementById('application-splash-wrapper');
    splash.parentElement.removeChild(splash);
}

pc.script.createLoadingScreen(function (app) {

    dg_createHTMLElements();

	//dg_updateElements();

    var setProgress = function (value) {
        dj_loading(value);
        
        var bar = document.getElementById('img_loadingbaroverlay');
        if(bar) {
            value = Math.min(1, Math.max(0, value));
            bar.style.width = value * 100 + '%';
        }
    };

    app.on('preload:end', function () {
        app.off('preload:progress');
    });
    app.on('preload:progress', setProgress);
    app.on('start', dg_hide_loading_pls);


});


document.title = "Crazy Knifes";

function dg_createHTMLElements()
{

    var createCss = function () {
        var css = [
            'body {',
            '    background-color: #2e6cf0;',
            '}',
            '',
            '#application-splash-wrapper {',
            '    position: absolute;',
            '    top: 0;',
            '    left: 0;',
            '    height: 100%;',
            '    width: 100%;',
            '    background-color: #2e6cf0;',
            '}',
            '',
            '#application-splash {',
            '    position: absolute;',
            '    top: calc(50% - 28px);',
            '    width: 264px;',
            '    left: calc(50% - 132px);',
            '}',
            '',
            '#img_pcLogoLoading  {',
				'transform: translate(-50%, -50%);',
                'position:absolute;',
                'left : 50%;',
                'top : 50%;',
                'width : 1px;',
                'height : 1px;',
            //'    border-radius: 25px;',
                'z-index: 10;',
                //'box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);',
            '}',
            '',
            '#img_loadingbar {',//style="border-radius: 25px; height: 8px; width: 450px; position:absolute; left : 0; top : 0; background-color:#EBEBEB; opacity : 0.0;z-index: 10;
            
            '    position:absolute;',
            '    border-radius: 25px;',
            '    height: 4px;',
            '    width: 450px;',
            '    left : 0;',
            '    top : 0;',
            '    background-color:#1848a2;',//#EBC700 // EBEBEB
            '    opacity : 0.1;',
            '    z-index: 10;',
            '}',
            '',
            '#img_loadingbaroverlay {', //border-radius: 25px; width:0%; height: 100%; background-color:#FA81A4;
            '    border-radius: 25px;',
            '    width: 5%;',
            '    height: 100%;',
            '    background-color: #fffd33;', // FFFFFF // FA81A4
            '}',
            '',
            '@media (max-width: 480px) {',
            '    #application-splash {',
            '        width: 170px;',
            '        left: calc(50% - 85px);',
            '    }',
            '}'
        ].join('\n');

        var style = document.createElement('style');
        style.type = 'text/css';
        if (style.styleSheet) {
            style.styleSheet.cssText = css;
        } else {
            style.appendChild(document.createTextNode(css));
        }

        document.head.appendChild(style);
    };

    createCss();




    var wrapper = document.createElement('div');
    wrapper.id = 'application-splash-wrapper';
    document.body.appendChild(wrapper);
    
    var logo = document.createElement('img');
    logo.id = 'img_pcLogoLoading';
    logo.src = 'files/performance/loading-1.webp?v=release-v17-level3';
    wrapper.appendChild(logo);




    logo.onload = function () {
    	dj_addLoadingElement('img_pcLogoLoading');
        dj_loading(0);
        //splash.style.display = 'block';
    };

    var container = document.createElement('div');
    container.id = 'img_loadingbar';
    wrapper.appendChild(container);

    var bar = document.createElement('div');
    bar.id = 'img_loadingbaroverlay';
    container.appendChild(bar);


    dj_addLoadingElement('img_pcLogoLoading');
	dj_addLoadingElement('img_loadingbar');
	dj_addLoadingElement('img_loadingbaroverlay');
	
	dj_loading(0);

};
