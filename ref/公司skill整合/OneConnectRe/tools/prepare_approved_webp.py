from pathlib import Path
import json,hashlib,shutil,zipfile,io
root=Path.cwd();src=root/'game'; stage=root/'analysis'/'webp_approved_stage_20261030'; assets=root/'analysis'/'WebP候选_20261030'; m=json.loads((assets/'integration_manifest.json').read_text(encoding='utf8'))
if stage.exists():raise SystemExit('stage already exists')
shutil.copytree(src,stage); data=(stage/'data.js').read_text(encoding='utf8');mapping={}
for row in m:
 old=stage/row['original'];new=stage/row['webp']; candidate=assets/new.name
 assert hashlib.sha256(old.read_bytes()).hexdigest()==row['source_sha256'];assert hashlib.sha256(candidate.read_bytes()).hexdigest()==row['webp_sha256']; assert row['original'] in data
 shutil.copy2(candidate,new);old.unlink();data=data.replace(row['original'],row['webp']);mapping[row['original']]=row['webp']
(stage/'data.js').write_text(data,encoding='utf8');(stage/'asset-formats.json').write_text(json.dumps(mapping,indent=2,ensure_ascii=False),encoding='utf8')
for n in ['dots-sheet0.png','line-sheet0.png','popfx-sheet0.png','popfx-sheet1.png']:
 assert (stage/'images'/n).read_bytes()==(root/'baseline'/'images'/n).read_bytes()
fs=[p for p in stage.rglob('*') if p.is_file()];b=io.BytesIO()
with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in fs:z.write(p,p.relative_to(stage).as_posix())
print('stage ready',len(mapping),'zip',len(b.getvalue()))
