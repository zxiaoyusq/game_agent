from pathlib import Path
p=Path('game/game.html');s=p.read_text(encoding='utf-8');s=s.replace('<script>\n\t    // Package-ID','<script src="host-adapter.js"></script>\n\t<script>\n\t    // Package-ID');p.write_text(s,encoding='utf-8')
p=Path('game/custom.js');s=p.read_text(encoding='utf-8');assert s.count('top.h5_sdk.showGameLoadingCompleted()')==1 and s.count('top.h5_sdk.showAd("Interstitial")')==2
s=s.replace('top.h5_sdk.showGameLoadingCompleted()','window.oneConnectHost.loadingCompleted()').replace('top.h5_sdk.showAd("Interstitial")','window.oneConnectHost.showAd("Interstitial")')
s=s.replace('trackEvent=function(e,n){return new Promise','trackEvent=function(e,n){window.oneConnectHost.emit("analytics."+e,n);return new Promise')
s=s.replace('trackScreen=function(e){','trackScreen=function(e){window.oneConnectHost.emit("screen."+e);')
p.write_text(s,encoding='utf-8')
