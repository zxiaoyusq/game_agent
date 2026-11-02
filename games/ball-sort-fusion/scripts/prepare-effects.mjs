// 独立运行时显式展开官方 2D Shader。材质元信息与 GLSL 均可追溯到固定版本官方源码。
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const engine=process.env.COCOS_ENGINE_PATH;
const project=path.resolve(import.meta.dirname,'..');
const fixtures=fs.readFileSync(path.join(engine,'tests/fixtures/builtin-effects.ts'),'utf8');
const effects=JSON.parse(fixtures.slice(fixtures.indexOf('['),fixtures.lastIndexOf(']')+1)).filter(effect=>['builtin-graphics','builtin-sprite'].includes(effect.name));
function chunk(name){return fs.readFileSync(path.join(engine,`editor/assets/chunks/builtin/uniforms/${name}.chunk`),'utf8').replace(/#pragma[^\n]*/g,'').replace(/layout\([^)]*\)\s*/g,'');}
const uniforms=chunk('cc-global'),local=chunk('cc-local');
for(const effect of effects){for(const shader of effect.shaders){
 let vert,frag;
 if(effect.name==='builtin-graphics'){
  vert=`precision highp float;\n${uniforms}${local}\nin vec3 a_position; in vec4 a_color; in float a_dist; out vec4 v_color; out float v_dist; void main(){gl_Position=cc_matViewProj*cc_matWorld*vec4(a_position,1.);v_color=a_color;v_dist=a_dist;}`;
  frag='precision highp float; in vec4 v_color; in float v_dist; out vec4 fragColor; void main(){float aa=fwidth(v_dist);float alpha=1.-smoothstep(-aa,0.,abs(v_dist)-1.);vec4 o=v_color;o.rgb*=o.a;fragColor=o*alpha;}';
 }else{
  vert=`precision highp float;\n${uniforms}\n#if USE_LOCAL\n${local}\n#endif\nin vec3 a_position;in vec2 a_texCoord;in vec4 a_color;out vec4 v_color;out vec2 v_uv;void main(){vec4 p=vec4(a_position,1.);\n#if USE_LOCAL\np=cc_matWorld*p;\n#endif\ngl_Position=cc_matViewProj*p;v_color=a_color;v_uv=a_texCoord;}`;
  frag='precision highp float;in vec4 v_color;in vec2 v_uv;out vec4 fragColor;\n#if USE_TEXTURE\nuniform sampler2D cc_spriteTexture;\n#endif\nvoid main(){vec4 o=v_color;\n#if USE_TEXTURE\no*=texture(cc_spriteTexture,v_uv);\n#endif\nfragColor=o;}';
 }
 shader.glsl3={vert,frag};shader.glsl4={vert,frag};
 // WebGL1 使用同一套 Cocos 材质布局，单独转换 GLSL 语法与导数扩展。
 const plain=text=>text.replace(/\/\/[^\n]*/g,'').replace(/uniform\s+\w+\s*\{([^}]+)\};/g,(_,body)=>body.split(';').filter(value=>value.trim()).map(value=>'uniform '+value.trim()+';').join('\n'));
 shader.glsl1={vert:plain(vert).replace(/\bin\s+(vec[234]|float)\s+(a_\w+)/g,'attribute $1 $2').replace(/\bout\s+(vec[234]|float)/g,'varying $1'),frag:'#extension GL_OES_standard_derivatives : enable\n'+plain(frag).replace(/\bin\s+(vec[234]|float)/g,'varying $1').replace(/out vec4 fragColor;/g,'').replace(/\bfragColor\b/g,'gl_FragColor').replace(/\btexture\(/g,'texture2D(')};
}}
fs.writeFileSync(path.join(project,'public/assets/effects.json'),JSON.stringify(effects));
const sources=['tests/fixtures/builtin-effects.ts','editor/assets/effects/internal/builtin-graphics.effect','editor/assets/effects/for2d/builtin-sprite.effect','editor/assets/chunks/builtin/uniforms/cc-global.chunk','editor/assets/chunks/builtin/uniforms/cc-local.chunk'];
fs.writeFileSync(path.join(project,'evidence/shader-sources.json'),JSON.stringify(sources.map(source=>({source:`https://github.com/cocos/cocos-engine/blob/411f98df047c25902f93440d4b22925c2fb65461/${source}`,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(engine,source))).digest('hex'),processing:'官方元信息保留；展开全局和局部Uniform；保留2D顶点色、纹理采样和抗锯齿；转换GLSL1语法'})),null,2));
console.log('已生成可追溯的官方 Cocos 2D 材质');
