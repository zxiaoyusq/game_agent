"""Compile verified timer overrides into a copy of the original Construct 2 data.
Validates level configuration and emits timer overrides for the Construct 2 runtime.
"""
import argparse, copy, json, os, shutil, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def compile_data(original, config):
    if not isinstance(config,dict): raise ValueError('config must be an object')
    if 'fallbackAutoShuffle' in config and config['fallbackAutoShuffle'] != 'free': raise ValueError('fallbackAutoShuffle must be free when specified')
    rows=config.get('levels')
    if not isinstance(rows,list): raise ValueError('levels must be a list')
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or not {'level','seconds'} <= set(row) or set(row)-{'level','seconds','board','theme','movement','generator','autoShuffle','timed','boardBackground','gravity','boardSize'}: raise ValueError('each entry requires level and seconds, and optional fields are board, theme, movement, generator, autoShuffle, timed, boardBackground and gravity')
        level,seconds=row['level'],row['seconds']
        if type(level) is not int or level<1 or level>100000: raise ValueError('level must be an integer from 1 to 100000')
        if type(seconds) is not int or seconds<1 or seconds>3600: raise ValueError('seconds must be an integer from 1 to 3600')
        if level in seen: raise ValueError('duplicate level')
        seen.add(level)
        if 'boardBackground' in row and row['boardBackground'] != 'hidden': raise ValueError('boardBackground must be hidden when specified')
        if 'timed' in row and type(row['timed']) is not bool: raise ValueError('timed must be boolean when specified')
        if 'autoShuffle' in row and row['autoShuffle'] not in ('free','original'): raise ValueError('autoShuffle must be free or original when specified')
        if 'movement' in row and row['movement'] not in ('static','gravity_down','gravity_up','gravity_left','gravity_right'): raise ValueError('invalid movement')
        size=row.get('boardSize')
        rows_count,cols_count=6,12
        if size is not None:
            if not isinstance(size,dict) or set(size)!={'rows','cols','itemSize','spacing','offsetX','offsetY'} or any(type(v) is not int for v in size.values()): raise ValueError('invalid boardSize fields')
            rows_count,cols_count=size['rows'],size['cols']
            if (rows_count,cols_count,size['itemSize'],size['spacing'],size['offsetX'],size['offsetY']) == (8,12,75,5,160,35): raise ValueError('unsafe legacy 8x12 preset; select the current 8x12 preset in the editor')
            if (rows_count,cols_count,size['itemSize'],size['spacing'],size['offsetX'],size['offsetY']) not in ((8,8,75,5,320,35),(8,10,75,5,240,35),(8,12,65,5,220,100)): raise ValueError('unsupported boardSize')
            if (rows_count,cols_count)==(8,8) and row.get('movement') != 'static': raise ValueError('8x8 boards currently require static movement')
            if (rows_count,cols_count)==(8,12) and row.get('movement') not in ('gravity_down','gravity_left','gravity_up','gravity_right','static'): raise ValueError('8x12 boards require static or a supported gravity direction')
            if (rows_count,cols_count)==(8,10) and row.get('movement') not in ('gravity_down','gravity_left','gravity_up','gravity_right','static'): raise ValueError('8x10 boards require static or a supported gravity direction')
        gravity_mode=row.get('movement') in ('gravity_down','gravity_up','gravity_left','gravity_right')
        bounds=row.get('gravity')
        if gravity_mode:
            if not isinstance(bounds,dict) or set(bounds)!={'top','left','rows','cols'} or any(type(bounds[k]) is not int for k in bounds) or bounds['top']<0 or bounds['left']<0 or bounds['rows']<1 or bounds['cols']<1 or bounds['top']+bounds['rows']>cols_count or bounds['left']+bounds['cols']>rows_count: raise ValueError('invalid gravity bounds')
        elif 'gravity' in row: raise ValueError('gravity bounds require gravity movement')
        if 'theme' in row and (type(row['theme']) is not int or not 0<=row['theme']<=3): raise ValueError('theme must be 0, 1, 2 or 3')
        if 'generator' in row:
            g=row['generator']
            if 'board' in row or row.get('movement') not in ('static','gravity_down','gravity_up','gravity_left','gravity_right'): raise ValueError('generated boards require configured movement and no fixed board')
            if not isinstance(g,dict) or set(g)-{'mask','typeCount','seed'} or not {'mask','typeCount'}<=set(g): raise ValueError('invalid generator fields')
            mask=g['mask']
            if not isinstance(mask,list) or len(mask)!=rows_count or any(not isinstance(line,list) or len(line)!=cols_count or any(type(v) is not int or v not in (0,1) for v in line) for line in mask): raise ValueError('generator mask dimensions must match boardSize')
            cells=sum(sum(line) for line in mask)
            if cells<2 or cells%2 or type(g['typeCount']) is not int or not 1<=g['typeCount']<=min(30,cells//2): raise ValueError('invalid generator mask or type count')
            if 'seed' in g and (type(g['seed']) is not int or not 0<=g['seed']<=4294967295): raise ValueError('invalid generator seed')
        if gravity_mode:
            shape=row.get('board') or (row.get('generator') or {}).get('mask')
            if not isinstance(shape,list) or len(shape)!=rows_count or any(not isinstance(r,list) or len(r)!=cols_count for r in shape): raise ValueError('gravity requires a valid board or generator mask')
            if any(shape[y][x] and not(bounds['left']<=y<bounds['left']+bounds['cols'] and bounds['top']<=cols_count-1-x<bounds['top']+bounds['rows']) for y in range(rows_count) for x in range(cols_count)): raise ValueError('board exceeds gravity bounds')
        if 'board' in row:
            board=row['board']
            if not isinstance(board,list) or len(board)!=rows_count or any(not isinstance(r,list) or len(r)!=cols_count for r in board): raise ValueError('board dimensions must match boardSize')
            cells=[v for r in board for v in r]
            if any(type(v) is not int or not 0<=v<=30 for v in cells): raise ValueError('board tiles must be integers from 0 to 30')
            if sum(v != 0 for v in cells)<2: raise ValueError('board must contain at least two tiles')
            if any(cells.count(v)%2 for v in set(cells) if v): raise ValueError('each tile must appear an even number of times')
        if row.get('theme')==3:
            if 'board' not in row and 'generator' not in row: raise ValueError('Ramadan theme requires a configured board or generator')
            if (row.get('generator') or {}).get('typeCount',0)>20 or any(v>20 for line in row.get('board',[]) for v in line):
                raise ValueError('Ramadan theme supports tile IDs 1 through 20')
    data=copy.deepcopy(original)
    sheets={x[0]:x for x in data['project'][6]}
    variables=[x for x in sheets['menuEvent'][1] if isinstance(x,list) and len(x)>3 and x[0]==1 and x[1]=='timerInit']
    if len(variables)!=1 or variables[0][3]!=300: raise ValueError('unexpected original timerInit')
    first=next((row['seconds'] for row in rows if row['level']==1),300)
    variables[0][3]=first
    event=sheets['gameEvent'][1][11][7][3]
    if event[5][0][-1] != [[1,[2,'nextLevel']]] or event[6][4][5] != [[11,'timer'],[7,[0,300]]]: raise ValueError('unexpected nextLevel structure')
    existing=set()
    def collect(o):
        if isinstance(o,list):
            for x in o: collect(x)
        elif type(o) is int:existing.add(o)
    collect(data['project'])
    sid=800000000000000
    def new_sid():
        nonlocal sid
        while sid in existing:sid+=1
        existing.add(sid);x=sid;sid+=1;return x
    # Replace the original Play -> theme picker transition with a direct start.
    menu=sheets['menuEvent'][1]
    try:
        play_actions=menu[18][7][0][6]
        old=play_actions[3]
        theme=copy.deepcopy(menu[18][7][1][7][1][6][0])
        start=copy.deepcopy(menu[18][7][1][7][1][6][4])
    except (IndexError, TypeError) as exc:
        raise ValueError('unexpected original menu structure') from exc
    if old[3]!=568856038478816 or theme[3]!=374024427033354 or start[3]!=206108413724904:
        raise ValueError('unexpected original menu actions')
    theme[3]=new_sid(); theme[5][1]=[7,[0,0]]
    start[3]=new_sid()
    play_actions[3:4]=[theme,start]
    injected=[]
    for row in sorted(rows,key=lambda x:x['level']):
        if row['level']==1:continue
        eid,cid,aid=new_sid(),new_sid(),new_sid()
        injected.append([0,None,False,None,eid,[[-1,29,None,0,False,False,False,cid,False,[[11,'level'],[8,0],[7,[0,row['level']]]]]],[[-1,27,None,aid,False,[[11,'timer'],[7,[0,row['seconds']]]]]]])
    event[7][0:0]=injected
    return data

def publish_outputs(outputs):
    """Publish staged files; restore prior bytes if a replace fails in-process."""
    before={path: path.read_bytes() if path.exists() else None for path,_ in outputs}
    prepared=[]
    published=[]
    try:
        for path,content in outputs:
            with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:
                prepared.append(Path(f.name))
                f.write(content)
        for (path,_),tmp in zip(outputs,prepared):
            os.replace(tmp,path)
            published.append(path)
    except Exception as exc:
        failures=[]
        for path in reversed(published):
            try:
                old=before[path]
                if old is None:
                    path.unlink(missing_ok=True)
                else:
                    with tempfile.NamedTemporaryFile('wb',dir=path.parent,delete=False) as f:
                        rollback=Path(f.name)
                        f.write(old)
                    try:
                        os.replace(rollback,path)
                    finally:
                        rollback.unlink(missing_ok=True)
            except Exception as rollback_exc:
                failures.append(str(path)+': '+str(rollback_exc))
        if failures:
            raise RuntimeError('publish failed and rollback failed: '+'; '.join(failures)) from exc
        raise
    finally:
        for tmp in prepared:
            tmp.unlink(missing_ok=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',default=str(ROOT/'config/levels.json'));ap.add_argument('--output',default=str(ROOT/'game/data.js'));a=ap.parse_args()
    source=json.loads((ROOT/'baseline/data.js').read_text(encoding='utf8')); config=json.loads(Path(a.config).read_text(encoding='utf-8-sig')); output=compile_data(source,config)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    # If the target game uses compressed art, retain its exact atlas mapping when
    # rebuilding Construct data. Baseline stays immutable and other targets opt in.
    asset_map_path=dest.with_name('asset-formats.json')
    if asset_map_path.exists():
        asset_map=json.loads(asset_map_path.read_text(encoding='utf-8-sig'))
        if not isinstance(asset_map,dict): raise ValueError('asset-formats.json must be an object')
        for original,replacement in asset_map.items():
            if not (isinstance(original,str) and isinstance(replacement,str) and original.startswith('images/') and replacement.startswith('images/') and '..' not in replacement and (dest.parent/replacement).is_file()):
                raise ValueError('invalid or missing compressed asset: '+str(replacement))
        hits=set()
        def map_assets(value):
            if isinstance(value,list): return [map_assets(x) for x in value]
            if isinstance(value,dict): return {k:map_assets(v) for k,v in value.items()}
            if isinstance(value,str) and value in asset_map:
                hits.add(value); return asset_map[value]
            return value
        output=map_assets(output)
        if hits != set(asset_map): raise ValueError('asset map includes paths absent from Construct data: '+str(sorted(set(asset_map)-hits)))
    # Reserve frames are optional for old projects, but required by any new IDs.
    extra=dest.parent/'images/tiles-reserve-test.png'
    if not extra.is_file(): extra=dest.parent/'images/tiles-reserve-test.webp'
    needs_extra=any((row.get('generator') or {}).get('typeCount',0)>20 or any(v>20 for line in row.get('board',[]) for v in line) for row in config['levels'])
    if needs_extra and not extra.is_file(): raise ValueError('extended tiles require reserve atlas')
    if extra.is_file():
        from PIL import Image
        with Image.open(extra) as image:
            if image.size!=(512,256) or image.format not in ('PNG','WEBP'): raise ValueError('invalid reserve atlas dimensions or format')
        animations=output['project'][3][5][7]
        if len(animations)!=3 or any(len(anim[7])!=20 for anim in animations): raise ValueError('unexpected tile animation layout')
        for anim in animations:
            for i in range(10): anim[7].append(['images/'+extra.name,extra.stat().st_size,1+(i%5)*98,1+(i//5)*98,96,96,1,0.5,0.5,[],[],0])
    atlas=dest.parent/'images/ramadan-tiles.webp'
    if any(row.get('theme')==3 for row in config['levels']) or atlas.is_file():
        if not atlas.is_file(): raise ValueError('Ramadan theme requires its atlas in the target game')
        from PIL import Image
        with Image.open(atlas) as image:
            if image.size!=(512,512) or image.mode!='RGBA': raise ValueError('invalid Ramadan atlas')
            atlas_pixels=image.tobytes()
        from build_ramadan_atlas import build as build_ramadan_atlas
        with tempfile.TemporaryDirectory(prefix='oc-ramadan-verify-') as scratch:
            expected=Path(scratch)/'approved.png'
            build_ramadan_atlas(expected)
            with Image.open(expected) as approved:
                if approved.convert('RGBA').tobytes()!=atlas_pixels: raise ValueError('Ramadan atlas differs from approved tiles')
        from ramadan_animation_candidate import add_ramadan_animation
        output=add_ramadan_animation(output,'images/ramadan-tiles.webp',atlas.stat().st_size,987654321234567)
    jsdest=dest.with_name('level-config.js')
    workerdest=dest.with_name('offline-worker.js')
    if dest in (jsdest, workerdest):
        raise ValueError('output cannot overwrite level-config.js or offline-worker.js')
    # Build a consistent candidate in a sibling directory.  The worker's manifest
    # must be calculated from the same candidate data/config that will be published.
    with tempfile.TemporaryDirectory(prefix='.oc-level-build-', dir=dest.parent.parent) as scratch:
        candidate=Path(scratch)/'game'
        if workerdest.is_file():
            shutil.copytree(dest.parent,candidate)
        else:
            candidate.mkdir()
        datafile=candidate/dest.name
        datafile.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')),encoding='utf8')
        configfile=candidate/'level-config.js'
        configfile.write_text('window.oneConnectLevels='+json.dumps(config,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
        outputs=[(dest,datafile.read_bytes()),(jsdest,configfile.read_bytes())]
        if workerdest.is_file():
            from build_offline_worker import build as build_offline_worker
            version,count=build_offline_worker(candidate)
            outputs.append((workerdest,(candidate/'offline-worker.js').read_bytes()))
        publish_outputs(outputs)
        if workerdest.is_file(): print('offline cache',version,'files',count)
    print('built',dest,'overrides',len(config['levels']))
if __name__=='__main__':main()

