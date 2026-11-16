(function(){
    'use strict';
    function decode(buffer){
        var view=new DataView(buffer),bytes=new Uint8Array(buffer);
        if(view.byteLength<8||view.getUint32(0,true)!==0x314d4343)throw new Error('Invalid CCM model');
        var length=view.getUint32(4,true),start=8+length;
        if(start>view.byteLength)throw new Error('Truncated CCM metadata');
        var model=JSON.parse(new TextDecoder().decode(bytes.subarray(8,start)));
        function restore(value){
            if(!value||typeof value!=='object')return value;
            if(value.__ccBuffer){
                var spec=value.__ccBuffer,offset=spec[0],count=spec[1],kind=spec[2],scale=spec[3];
                var size={f32:4,i16:2,i32:4,d16:2,d32:4}[kind];
                if(!size||!Number.isSafeInteger(count)||count<0||!Number.isSafeInteger(offset)||offset<0||start+offset+count*size>view.byteLength||!scale)throw new Error('Invalid CCM buffer');
                var out=new Array(count),last=0;
                for(var i=0;i<count;i++){
                    var p=start+offset+i*size,v;
                    if(kind==='f32')v=view.getFloat32(p,true);
                    else if(kind==='i16')v=Math.fround(view.getInt16(p,true)/scale);
                    else if(kind==='i32')v=Math.fround(view.getInt32(p,true)/scale);
                    else {v=kind==='d16'?view.getUint16(p,true):view.getUint32(p,true);last+=(v&1)?-(v+1)/2:v/2;v=last;}
                    if(!Number.isFinite(v))throw new Error('Invalid CCM value');out[i]=v;
                }
                return out;
            }
            Object.keys(value).forEach(function(key){value[key]=restore(value[key]);});return value;
        }
        return restore(model);
    }
    var load=pc.ModelHandler.prototype.load;
    pc.ModelHandler.prototype.load=function(url,callback,asset){
        var source=typeof url==='string'?url:url.load;
        if(!/\.ccm(?:\?|$)/.test(source))return load.call(this,url,callback,asset);
        var owner=this,original=(typeof url==='string'?url:url.original).replace(/\.ccm(?=\?|$)/,'.json').split('?')[0];
        fetch(source).then(function(response){if(!response.ok)throw new Error('Model HTTP '+response.status);return response.arrayBuffer();}).then(decode).then(function(data){
            return new Promise(function(resolve,reject){
                // Pinned PlayCanvas 1.69.2 parses models in load(), while open()
                // is an identity function. Reuse its registered JSON parser.
                var entry=owner._parsers.find(function(p){return p.decider(original,data);});
                if(!entry)throw new Error('Missing JSON model parser');
                entry.parser.parse(data,function(error,model){if(error)reject(error);else resolve(model);},asset);
            });
        }).then(function(model){callback(null,model);},function(error){callback(String(error));});
    };
    window.CrazyKnifesModelBuffers={decode:decode};
}());
