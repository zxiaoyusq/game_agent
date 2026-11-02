// Spine 3.8 runtime load/play QA for db2spine output (116 groups)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const args = process.argv.slice(2);
const OUT = args[0] || 'E:\\Gameprogram\\blast-block-dragonbones-spine';
const RUNTIME = args[1] || 'E:\\Gameprogram\\blast-block-spine\\lib\\spine-player.js';
const REPORT = args[2] || path.join(__dirname, 'qa_spine_report.json');

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(RUNTIME, 'utf8'), sandbox, { filename: 'spine-player.js' });
const spine = sandbox.spine;
if (!spine || !spine.SkeletonJson) throw new Error('runtime load failed');
console.log('runtime OK: SkeletonJson=' + !!spine.SkeletonJson + ' TextureAtlas=' + !!spine.TextureAtlas);

function pngSize(p) {
  const b = fs.readFileSync(p);
  if (b.length < 24 || b.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG: ' + p);
  return { width: b.readUInt32BE(16), height: b.readUInt32BE(20) };
}

const groups = fs.readdirSync(OUT).filter((d) => {
  if (d === 'preview') return false;
  return fs.statSync(path.join(OUT, d)).isDirectory();
}).sort();

const report = { runtime: '3.8', total: 0, ok: [], fail: [], warnings: [] };

for (const g of groups) {
  const dir = path.join(OUT, g);
  const jp = path.join(dir, g + '.json');
  const ap = path.join(dir, g + '.atlas');
  if (!fs.existsSync(jp) || !fs.existsSync(ap)) {
    report.fail.push({ group: g, error: 'missing json/atlas' });
    continue;
  }
  let rec = { group: g };
  try {
    const json = JSON.parse(fs.readFileSync(jp, 'utf8'));
    const atlasText = fs.readFileSync(ap, 'utf8');
    const atlas = new spine.TextureAtlas(atlasText, (name) => {
      const img = path.join(dir, name);
      if (!fs.existsSync(img)) throw new Error('atlas page image missing: ' + name);
      const sz = pngSize(img);
      return new spine.FakeTexture({ width: sz.width, height: sz.height });
    });
    const loader = new spine.AtlasAttachmentLoader(atlas);
    const skelJson = new spine.SkeletonJson(loader);
    const data = skelJson.readSkeletonData(json);
    const skeleton = new spine.Skeleton(data);
    const stateData = new spine.AnimationStateData(data);
    const state = new spine.AnimationState(stateData);
    const anims = [];
    for (const anim of data.animations) {
      state.setAnimation(0, anim.name, true);
      const steps = Math.max(1, Math.ceil(anim.duration * 30));
      for (let i = 0; i < steps; i++) {
        state.update(1 / 30);
        state.apply(skeleton);
        skeleton.updateWorldTransform();
      }
      skeleton.setToSetupPose();
      anims.push({ name: anim.name, duration: +anim.duration.toFixed(3) });
    }
    atlas.dispose();
    rec.anims = anims;
    rec.bones = data.bones.length;
    rec.slots = data.slots.length;
    rec.skins = data.skins.length;
    rec.spineVersion = json.skeleton && json.skeleton.spine;
    rec.pages = atlas.pages.length;
    rec.regions = atlas.regions.length;
    // count attachments declared in skins and verify each resolves to an atlas region
    let texDeclared = 0, texResolved = 0, nonTex = 0;
    for (const skin of data.skins) {
      for (const slotKey of Object.keys(skin.attachments)) {
        const slot = skin.attachments[slotKey];
        for (const nameKey of Object.keys(slot)) {
          const att = slot[nameKey];
          if (att instanceof spine.RegionAttachment || att instanceof spine.MeshAttachment) {
            texDeclared++;
            if (atlas.findRegion(att.path || att.name)) texResolved++;
          } else {
            nonTex++;
          }
        }
      }
    }
    rec.attachmentsTex = texDeclared;
    rec.attachmentsResolved = texResolved;
    rec.attachmentsNonTex = nonTex;
    report.ok.push(rec);
  } catch (e) {
    report.fail.push({ group: g, error: String(e && e.message || e) });
  }
}

report.total = groups.length;
fs.writeFileSync(REPORT, JSON.stringify(report, null, 1), 'utf8');
console.log('TOTAL', report.total, 'OK', report.ok.length, 'FAIL', report.fail.length);
for (const f of report.fail) console.log('FAIL', f.group, f.error);
const totalAnims = report.ok.reduce((s, r) => s + r.anims.length, 0);
console.log('animations played:', totalAnims);
