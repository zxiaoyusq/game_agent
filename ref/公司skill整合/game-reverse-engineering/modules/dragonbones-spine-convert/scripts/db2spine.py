# -*- coding: utf-8 -*-
"""
DragonBones(DB) 5.0 / 5.5 -> Spine 3.8 JSON + Atlas 转换器

输入: E:\\Gameprogram\\blast-block-dragonbones\\<group>\\
      (*_ske.json / *_ske-lite.json + *_tex*.json + *.png)
输出: E:\\Gameprogram\\blast-block-dragonbones-spine\\<group>\\
      (<group>.json + <group>.atlas + png + preview.html + index.json)

映射依据(已对游戏运行时 C++ 源码逐项核对):
  * DB JSON 为 y-up(yDown=false), rotation = skY, skew = skX - skY, 正角 = 逆时针
  * Spine: rotation = skY, shearX = skX - skY, scaleX/Y = scX/scY
  * slot color / colorFrame 为 0-100 百分比 -> Spine 0-255 十六进制
  * curve = [x1,y1,x2,y2] 三次贝塞尔控制点, 与 Spine 完全一致
  * tweenEasing 缺失/null -> "stepped"; ==0 -> 线性
  * ffd: DB offset 为 float 索引, vertices 为增量 -> Spine deform 直接映射
  * zOrder: [slotIndex, offset, ...] 对 -> Spine drawOrder offsets
  * 图集 offset = (-frameX, frameHeight - height + frameY)(已用原生 Spine 验证)
  * mesh uvs 为区域相对(top-left origin) -> Spine regionUV 翻转 v
  * 同名区域跨页: 与 DB 运行时一致, 第一页先到先得
"""

import base64
import argparse
import json
import math
import re
import shutil
import struct
from pathlib import Path

SRC = Path(r'E:\Gameprogram\blast-block-dragonbones')
OUT = Path(r'E:\Gameprogram\blast-block-dragonbones-spine')
LIB = Path(r'E:\Gameprogram\blast-block-spine\lib')

FRAC = 3


_CURVE_ARRAY = re.compile(
    r'"curve":\[(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),'
    r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),'
    r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),'
    r'(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\]')


def fix_curves(text):
    """Spine 3.8 JSON 的曲线是 'curve' 数字 + 可选 c2/c3/c4 四个字段,
    不接受 4.x 的 'curve':[x1,y1,x2,y2] 数组写法。这里做无损改写:
    [a,b,c,d] -> "curve":a,"c2":b,"c3":c,"c4":d
    """
    return _CURVE_ARRAY.sub(
        r'"curve":\1,"c2":\2,"c3":\3,"c4":\4', text)


def rnd(v, frac=FRAC):
    if v is None:
        return v
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    if abs(f) < 5e-11:
        return 0.0
    return round(f, frac)


def find_ske(gd):
    for pat in ('*_ske.json', '*_ske-lite.json'):
        hits = sorted(gd.glob(pat))
        if hits:
            return hits[0]
    return None


def find_tex(gd):
    hits = sorted(gd.glob('*_tex*.json'))
    out = []
    for t in hits:
        png = t.with_suffix('.png')
        if not png.exists():
            try:
                d = json.loads(t.read_text(encoding='utf-8'))
                cand = gd / os_path_basename(d.get('imagePath', ''))
                if cand.exists():
                    png = cand
            except Exception:
                pass
        out.append((t, png))
    return out


def os_path_basename(p):
    return p.replace('\\', '/').split('/')[-1]


def png_size(path):
    try:
        with open(path, 'rb') as f:
            head = f.read(24)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', head[16:24])
    except OSError:
        pass
    return None


def db_rot(t):
    skX = t.get('skX', 0) or 0
    skY = t.get('skY', 0) or 0
    scX = t.get('scX', 1)
    scY = t.get('scY', 1)
    if scX is None:
        scX = 1
    if scY is None:
        scY = 1
    return {
        'rotation': rnd(skY),
        'shearX': rnd(skX - skY),
        'scaleX': rnd(scX),
        'scaleY': rnd(scY),
        'x': rnd(t.get('x', 0)),
        'y': rnd(t.get('y', 0)),
    }


def color_to_hex(c):
    def ch(k):
        v = c.get(k, 100)
        if v is None:
            v = 100
        return max(0, min(255, round(v * 255 / 100)))
    return '%02x%02x%02x%02x' % (ch('rM'), ch('gM'), ch('bM'), ch('aM'))


def curve_of(frame):
    if isinstance(frame, dict):
        c = frame.get('curve')
        if isinstance(c, list) and len(c) >= 4:
            return [rnd(x, 4) for x in c[:4]]
        te = frame.get('tweenEasing')
        if te is None:
            return 'stepped'
        if te == 0:
            return None
        return [0.25, 0, 0.75, 1]
    return None


def transform_delta(dx, dy, trans):
    if not trans or (trans['rotation'] == 0 and trans['scaleX'] == 1
                     and trans['scaleY'] == 1 and trans['shearX'] == 0):
        return rnd(dx), rnd(dy)
    rot = math.radians(trans['rotation'])
    cos = math.cos(rot)
    sin = math.sin(rot)
    sx = trans['scaleX']
    sy = trans['scaleY']
    return rnd(dx * sx * cos - dy * sy * sin), rnd(dx * sx * sin + dy * sy * cos)


def bake_vertex(vx, vy, trans):
    if not trans:
        return rnd(vx), rnd(vy)
    rot = math.radians(trans['rotation'])
    cos = math.cos(rot)
    sin = math.sin(rot)
    sx = trans['scaleX']
    sy = trans['scaleY']
    return rnd(vx * sx * cos - vy * sy * sin + trans['x']), \
        rnd(vx * sx * sin + vy * sy * cos + trans['y'])


class TimelineBuilder:
    def __init__(self, fps, anim_duration):
        self.fps = fps
        self.anim_duration = anim_duration

    def _time(self, t):
        return round(t / self.fps, 4)

    def build(self, frames, current, extract, curve_ok=True):
        """frames: DB 帧列表; current: 状态 dict(会被原地更新);
        extract(frame, current) -> dict(变化分量)|None"""
        keys = []
        t = 0
        n = len(frames)
        for i, fr in enumerate(frames):
            if isinstance(fr, dict):
                upd = extract(fr, current)
                if upd:
                    current.update(upd)
                item = {'time': self._time(t)}
                item.update(current)
                if i < n - 1 and curve_ok:
                    c = curve_of(fr)
                    if c is not None:
                        item['curve'] = c
                keys.append(item)
                t += fr.get('duration', 1) or 0
        # 末尾保持帧 -> Spine 动画时长与 DB 一致(DB 最后一帧时长自动补足)
        end_t = self._time(self.anim_duration)
        if keys and keys[-1]['time'] < end_t:
            item = {'time': end_t}
            item.update(current)
            keys.append(item)
        return keys


def convert_group(g, report):
    gd = SRC / g
    ske_path = find_ske(gd)
    if ske_path is None:
        report['skipped'].append((g, 'no ske json'))
        return None
    tex_list = find_tex(gd)
    if not tex_list:
        report['skipped'].append((g, 'no tex json'))
        return None
    db = json.loads(ske_path.read_text(encoding='utf-8'))
    version = str(db.get('version', '?'))
    arm = db['armature'][0]
    fps = float(arm.get('frameRate') or db.get('frameRate') or 30)

    # ---------- 图集 ----------
    pages = []
    region_names = set()
    dup_regions = []
    for tex_path, png_path in tex_list:
        d = json.loads(tex_path.read_text(encoding='utf-8'))
        regions = []
        for st in d.get('SubTexture', []):
            nm = st.get('name')
            if nm in region_names:
                dup_regions.append((nm, tex_path.name))
                continue
            region_names.add(nm)
            regions.append(st)
        real = png_size(png_path) if png_path and png_path.exists() else None
        pages.append({
            'png': png_path.name if png_path and png_path.exists() else None,
            'width': real[0] if real else d.get('width', 0),
            'height': real[1] if real else d.get('height', 0),
            'regions': regions,
        })
    if not region_names:
        report['skipped'].append((g, 'empty atlas'))
        return None

    # ---------- 骨骼 ----------
    bone_by_name = {}
    for b in arm.get('bone', []):
        name = b.get('name')
        if not name:
            continue
        t = db_rot(b.get('transform', {}))
        bone_by_name[name] = {
            'name': name,
            'parent': b.get('parent'),
            'x': t['x'], 'y': t['y'],
            'rotation': t['rotation'],
            'scaleX': t['scaleX'], 'scaleY': t['scaleY'],
            'shearX': t['shearX'],
            'length': rnd(b.get('length', 0)),
        }
    ordered = []
    visited = set()

    def visit(name, stack):
        if name in visited or name in stack:
            return
        stack.add(name)
        par = bone_by_name[name]['parent']
        if par and par in bone_by_name:
            visit(par, stack)
        visited.add(name)
        ordered.append(name)

    for name in bone_by_name:
        visit(name, set())
    root_name = None
    bones = []
    for name in ordered:
        b = bone_by_name[name]
        par = b['parent']
        par_out = par if (par and par in bone_by_name) else None
        bones.append({
            'name': name,
            'parent': par_out,
            'x': b['x'], 'y': b['y'],
            'rotation': b['rotation'],
            'scaleX': b['scaleX'], 'scaleY': b['scaleY'],
            'shearX': b['shearX'],
        })
        if b['length']:
            bones[-1]['length'] = b['length']
        if par_out is None and root_name is None:
            root_name = name

    # ---------- 槽位 ----------
    skin = (arm.get('skin') or [{}])[0]
    slot_display = {}
    for ss in skin.get('slot', []):
        slot_display[ss.get('name')] = ss.get('display', [])
    slots_out = []
    slot_index = {}
    for i, s in enumerate(arm.get('slot', [])):
        name = s.get('name')
        parent = s.get('parent')
        if parent not in bone_by_name:
            parent = root_name
        slot = {'name': name, 'bone': parent}
        disp = slot_display.get(name, [])
        di = s.get('displayIndex', 0)
        if di is None:
            di = 0
        if 0 <= di < len(disp):
            slot['attachment'] = disp[di].get('name')
        if s.get('blendMode') == 'add':
            slot['blend'] = 'additive'
        col = color_to_hex(s.get('color', {}))
        if col != 'ffffffff':
            slot['color'] = col
        slots_out.append(slot)
        slot_index[name] = i

    # ---------- 皮肤/附件 ----------
    att_missing = []
    attachments = {}
    mesh_trans = {}

    def find_region(path):
        for pg in pages:
            for st in pg['regions']:
                if st.get('name') == path:
                    return st
        return None

    for ss in skin.get('slot', []):
        sname = ss.get('name')
        amap = attachments.setdefault(sname, {})
        for disp in ss.get('display', []):
            aname = disp.get('name')
            dtype = disp.get('type') or 'image'
            path = disp.get('path') or aname
            trans = disp.get('transform')
            t = db_rot(trans) if trans else None
            if t and t['rotation'] == 0 and t['shearX'] == 0 and t['scaleX'] == 1 \
                    and t['scaleY'] == 1 and t['x'] == 0 and t['y'] == 0:
                t = None
            sub = find_region(path)
            if sub is None:
                att_missing.append((sname, aname, path))
                continue
            if dtype == 'image':
                ow = sub.get('frameWidth') or sub.get('width', 0)
                oh = sub.get('frameHeight') or sub.get('height', 0)
                att = {'name': aname, 'path': path, 'width': rnd(ow), 'height': rnd(oh)}
                if t:
                    att['x'] = t['x']
                    att['y'] = t['y']
                    att['rotation'] = t['rotation']
                    att['scaleX'] = t['scaleX']
                    att['scaleY'] = t['scaleY']
                amap[aname] = att
            elif dtype == 'mesh':
                uvs = disp.get('uvs', [])
                verts = disp.get('vertices', [])
                spine_uvs = []
                for i in range(0, len(uvs), 2):
                    spine_uvs.append(rnd(uvs[i], 4))
                    spine_uvs.append(rnd(1 - uvs[i + 1], 4))
                spine_verts = []
                for i in range(0, len(verts), 2):
                    vx, vy = bake_vertex(verts[i], verts[i + 1], t)
                    spine_verts.append(vx)
                    spine_verts.append(vy)
                att = {
                    'type': 'mesh',
                    'name': aname,
                    'path': path,
                    'uvs': spine_uvs,
                    'triangles': [int(x) for x in disp.get('triangles', [])],
                    'vertices': spine_verts,
                    'width': rnd(disp.get('width', 0)),
                    'height': rnd(disp.get('height', 0)),
                }
                if len(verts) // 2 > 0:
                    att['hull'] = len(verts) // 2
                if disp.get('edges'):
                    att['edges'] = [int(x) for x in disp['edges']]
                amap[aname] = att
                if t:
                    mesh_trans[(sname, aname)] = t
            else:
                report['warn'].append(
                    (g, 'unsupported display type %s slot=%s disp=%s' % (dtype, sname, aname)))
    skins_out = [{'name': 'default', 'attachments': attachments}] if attachments else []

    # ---------- 动画 ----------
    anims_out = {}
    for anim in arm.get('animation', []):
        aname = anim.get('name')
        adur = float(anim.get('duration', 0))
        builder = TimelineBuilder(fps, adur)
        bones_anim = {}
        slots_anim = {}
        deform_anim = {}
        draworder = []

        for tl in anim.get('bone', []):
            bname = tl.get('name')
            if bname not in bone_by_name:
                continue
            setup = bone_by_name[bname]
            bm = bones_anim.setdefault(bname, {})
            if 'translateFrame' in tl:
                keys = builder.build(
                    tl['translateFrame'], {'x': setup['x'], 'y': setup['y']},
                    lambda fr, c: ({'x': rnd(fr['x']), 'y': rnd(fr['y'])}
                                   if 'x' in fr and 'y' in fr else
                                   {'x': rnd(fr['x'])} if 'x' in fr else
                                   {'y': rnd(fr['y'])} if 'y' in fr else None))
                bm['translate'] = keys
            if 'scaleFrame' in tl:
                keys = builder.build(
                    tl['scaleFrame'], {'x': setup['scaleX'], 'y': setup['scaleY']},
                    lambda fr, c: ({'x': rnd(fr['x']), 'y': rnd(fr['y'])}
                                   if 'x' in fr and 'y' in fr else
                                   {'x': rnd(fr['x'])} if 'x' in fr else
                                   {'y': rnd(fr['y'])} if 'y' in fr else None))
                bm['scale'] = keys
            if 'rotateFrame' in tl:
                keys = builder.build(
                    tl['rotateFrame'], {'angle': setup['rotation']},
                    lambda fr, c: {'angle': rnd(fr['rotate'])} if 'rotate' in fr else None)
                bm['rotate'] = keys
            if 'frame' in tl:
                tr_keys = builder.build(
                    tl['frame'], {'x': setup['x'], 'y': setup['y']},
                    lambda fr, c: ({'x': rnd(fr['transform']['x']), 'y': rnd(fr['transform']['y'])}
                                   if 'transform' in fr and 'x' in fr['transform'] and 'y' in fr['transform']
                                   else {'x': rnd(fr['transform']['x'])}
                                   if 'transform' in fr and 'x' in fr['transform']
                                   else {'y': rnd(fr['transform']['y'])}
                                   if 'transform' in fr and 'y' in fr['transform'] else None))
                sc_keys = builder.build(
                    tl['frame'], {'x': setup['scaleX'], 'y': setup['scaleY']},
                    lambda fr, c: ({'x': rnd(fr['transform']['scX']), 'y': rnd(fr['transform']['scY'])}
                                   if 'transform' in fr and 'scX' in fr['transform'] and 'scY' in fr['transform']
                                   else {'x': rnd(fr['transform']['scX'])}
                                   if 'transform' in fr and 'scX' in fr['transform']
                                   else {'y': rnd(fr['transform']['scY'])}
                                   if 'transform' in fr and 'scY' in fr['transform'] else None))
                rot_keys = builder.build(
                    tl['frame'], {'angle': setup['rotation']},
                    lambda fr, c: {'angle': rnd(fr['transform']['skY'])}
                    if 'transform' in fr and 'skY' in fr['transform'] else None)
                if any('x' in k or 'y' in k for k in tr_keys):
                    bm['translate'] = tr_keys
                if any('x' in k or 'y' in k for k in sc_keys):
                    bm['scale'] = sc_keys
                if any('angle' in k for k in rot_keys):
                    bm['rotate'] = rot_keys

        slot_defaults = {}
        for s in arm.get('slot', []):
            slot_defaults[s.get('name')] = (s.get('displayIndex', 0), s.get('color', {}))

        for tl in anim.get('slot', []):
            sname = tl.get('name')
            if sname not in slot_index:
                continue
            sm = slots_anim.setdefault(sname, {})
            disp = slot_display.get(sname, [])
            di0, col0 = slot_defaults.get(sname, (0, {}))
            if di0 is None:
                di0 = 0
            cur_att = {'name': disp[di0].get('name')} if 0 <= di0 < len(disp) else {'name': None}

            def ext_disp(fr, c):
                if 'value' not in fr:
                    return None
                v = fr['value']
                c['name'] = disp[v].get('name') if 0 <= v < len(disp) else None
                return {'name': c['name']}

            def ext_disp50(fr, c):
                if 'displayIndex' not in fr:
                    return None
                v = fr['displayIndex']
                c['name'] = disp[v].get('name') if 0 <= v < len(disp) else None
                return {'name': c['name']}

            if 'displayFrame' in tl:
                keys = builder.build(tl['displayFrame'], cur_att, ext_disp, curve_ok=False)
                sm['attachment'] = keys
            elif 'frame' in tl:
                keys = builder.build(tl['frame'], cur_att, ext_disp50, curve_ok=False)
                sm['attachment'] = keys

            cur_col = {'color': color_to_hex(col0)}

            def ext_col(fr, c):
                v = fr.get('value')
                if not v:
                    return None
                base = {'rM': 100, 'gM': 100, 'bM': 100, 'aM': 100}
                for ch in ('rM', 'gM', 'bM', 'aM'):
                    if ch in v:
                        base[ch] = v[ch]
                c['color'] = color_to_hex(base)
                return {'color': c['color']}

            def ext_col50(fr, c):
                v = fr.get('color')
                if not v:
                    return None
                base = {'rM': 100, 'gM': 100, 'bM': 100, 'aM': 100}
                for ch in ('rM', 'gM', 'bM', 'aM'):
                    if ch in v:
                        base[ch] = v[ch]
                c['color'] = color_to_hex(base)
                return {'color': c['color']}

            if 'colorFrame' in tl:
                keys = builder.build(tl['colorFrame'], cur_col, ext_col)
                sm['color'] = keys
            elif 'frame' in tl:
                keys = builder.build(tl['frame'], cur_col, ext_col50)
                sm['color'] = keys

        for tl in anim.get('ffd', []):
            sname = tl.get('slot')
            aname = tl.get('name')
            if sname not in slot_index:
                continue
            trans = mesh_trans.get((sname, aname))
            frames = []
            t = 0
            fl = tl.get('frame', [])
            for i, fr in enumerate(fl):
                item = {'time': round(t / fps, 4)}
                if fr.get('vertices'):
                    item['offset'] = int(fr.get('offset', 0))
                    varr = fr['vertices']
                    if trans:
                        vs = []
                        for j in range(0, len(varr), 2):
                            dx, dy = transform_delta(varr[j], varr[j + 1], trans)
                            vs.append(dx)
                            vs.append(dy)
                    else:
                        vs = [rnd(x, 4) for x in varr]
                    item['vertices'] = vs
                if i < len(fl) - 1:
                    c = curve_of(fr)
                    if c is not None:
                        item['curve'] = c
                frames.append(item)
                t += fr.get('duration', 1) or 0
            if frames:
                deform_anim.setdefault('default', {}).setdefault(sname, {})[aname] = frames

        zf = anim.get('zOrder')
        if zf and zf.get('frame'):
            t = 0
            zframes = []
            for fr in zf['frame']:
                offsets = []
                zo = fr.get('zOrder') or []
                for j in range(0, len(zo), 2):
                    idx = int(zo[j])
                    off = int(zo[j + 1])
                    if 0 <= idx < len(slots_out):
                        offsets.append({'slot': slots_out[idx]['name'], 'offset': off})
                zframes.append({'time': round(t / fps, 4), 'offsets': offsets})
                t += fr.get('duration', 1) or 0
            draworder = zframes

        anim_obj = {}
        if bones_anim:
            anim_obj['bones'] = bones_anim
        if slots_anim:
            anim_obj['slots'] = slots_anim
        if deform_anim:
            anim_obj['deform'] = deform_anim
        if draworder:
            anim_obj['drawOrder'] = draworder
        anims_out[aname] = anim_obj

    aabb = arm.get('aabb', {})
    skel = {
        'hash': 'db2spine-%s' % re.sub(r'[^A-Za-z0-9]', '_', g)[-48:],
        'spine': '3.8.95',
        'x': rnd(aabb.get('x', 0)),
        'y': rnd(aabb.get('y', 0)),
        'width': rnd(aabb.get('width', 0)),
        'height': rnd(aabb.get('height', 0)),
        'images': '',
        'fps': int(round(fps)),
    }
    data = {
        'skeleton': skel,
        'bones': bones,
        'slots': slots_out,
        'skins': skins_out,
        'animations': anims_out,
    }
    return {
        'data': data,
        'pages': pages,
        'version': version,
        'dup_regions': dup_regions,
        'att_missing': att_missing,
    }


def write_atlas(path, pages):
    blocks = []
    for pg in pages:
        lines = []
        lines.append(pg['png'] or '__missing__.png')
        lines.append('size: %d,%d' % (pg['width'], pg['height']))
        lines.append('format: RGBA8888')
        lines.append('filter: Linear,Linear')
        lines.append('repeat: none')
        for st in pg['regions']:
            w = st.get('width', 0)
            h = st.get('height', 0)
            fw = st.get('frameWidth')
            fh = st.get('frameHeight')
            fx = st.get('frameX', 0)
            fy = st.get('frameY', 0)
            if fw and fh:
                orig = '%d,%d' % (fw, fh)
                off = '%d,%d' % (-fx, (fh - h) + fy)
            else:
                orig = '%d,%d' % (w, h)
                off = '0,0'
            lines.append(st.get('name'))
            lines.append('  rotate: %s' % ('true' if st.get('rotate') else 'false'))
            lines.append('  xy: %d, %d' % (st.get('x', 0), st.get('y', 0)))
            lines.append('  size: %d, %d' % (w, h))
            lines.append('  orig: ' + orig)
            lines.append('  offset: ' + off)
            lines.append('  index: -1')
        blocks.append('\n'.join(lines))
    path.write_text('\n\n'.join(blocks), encoding='utf-8')


PREVIEW_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  html,body{height:100%;margin:0;background:#17191f;color:#e8eaf0;font-family:"Microsoft YaHei",system-ui,sans-serif;overflow:hidden}
  #stage{width:100%;height:100%}
  #bar{position:fixed;left:10px;top:10px;background:rgba(20,22,28,.85);border:1px solid #333845;border-radius:8px;
    padding:8px 12px;font-size:12px;z-index:9;max-width:70vw;line-height:1.6}
  #bar b{color:#4cc2ff}
  #bar .anim{color:#9aa1b0}
  #err{color:#ff6b6b}
</style>
</head>
<body>
<div id="bar">
  <div><b>{name}</b>  <span class="anim">{anim_count} 个动画 · {version}</span></div>
  <div id="err"></div>
</div>
<div id="stage"></div>
<script src="lib/spine-player.js"></script>
<script>
const CFG = __CFG__;
let idx = 0;
function loadAnim(){
  const el = document.getElementById('stage');
  el.innerHTML = '';
  const anims = CFG.anims;
  if (!anims.length) return;
  const anim = anims[idx % anims.length];
  document.querySelector('#bar .anim').textContent =
    (idx % anims.length + 1) + '/' + anims.length + ' · ' + anim + ' · ' + CFG.version;
  try {
    new spine.SpinePlayer(el, {
      jsonUrl: CFG.jsonUrl,
      atlasUrl: CFG.atlasUrl,
      animation: anim,
      skin: null,
      alpha: true,
      premultipliedAlpha: false,
      backgroundColor: '#00000000',
      viewport: CFG.bounds,
      showControls: true,
      success: function(w){ w.animationState.timeScale = 1; const a = w.animationState.getCurrent(0); if(a) a.loop = true; },
      error: function(w, msg){ document.getElementById('err').textContent = '加载失败: ' + msg; }
    });
  } catch(e) { document.getElementById('err').textContent = '初始化失败: ' + e; }
}
setInterval(function(){ idx++; loadAnim(); }, 6000);
loadAnim();
</script>
</body>
</html>
"""


def write_preview(outdir, name, json_bytes, atlas_bytes, png_bytes_list, anims, version, bounds):
    lines = atlas_bytes.decode('utf-8', errors='ignore').splitlines()
    png_iter = iter(png_bytes_list)
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s and not s.startswith(('#', ' ', '\t')) and ':' not in s:
            try:
                png_bytes = next(png_iter)
                lines[i] = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode('ascii')
            except StopIteration:
                break
    atlas_text = '\n'.join(lines)
    cfg = {
        'jsonUrl': 'data:application/json;base64,' + base64.b64encode(json_bytes).decode('ascii'),
        'atlasUrl': 'data:text/plain;base64,' + base64.b64encode(atlas_text.encode('utf-8')).decode('ascii'),
        'anims': anims,
        'version': version,
        'bounds': bounds,
    }
    html = (PREVIEW_TEMPLATE
            .replace('__CFG__', json.dumps(cfg, ensure_ascii=False))
            .replace('{title}', name)
            .replace('{name}', name)
            .replace('{anim_count}', str(len(anims)))
            .replace('{version}', version))
    (outdir / 'preview.html').write_text(html, encoding='utf-8')


def main():
    global SRC, OUT
    ap = argparse.ArgumentParser(description='DragonBones 5.0/5.5 -> Spine 3.8 converter')
    ap.add_argument('--src', default=str(SRC), help='input DragonBones root dir')
    ap.add_argument('--out', default=str(OUT), help='output Spine root dir')
    args = ap.parse_args()
    SRC = Path(args.src)
    OUT = Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    groups = sorted([d.name for d in SRC.iterdir() if d.is_dir()])
    report = {'ok': [], 'warn': [], 'skipped': []}
    manifest = []
    for g in groups:
        res = convert_group(g, report)
        if res is None:
            continue
        outdir = OUT / g
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / (g + '.json')).write_text(
            fix_curves(json.dumps(res['data'], ensure_ascii=False, separators=(',', ':'))),
            encoding='utf-8')
        write_atlas(outdir / (g + '.atlas'), res['pages'])
        png_bytes_list = []
        for pg in res['pages']:
            if pg['png']:
                src = SRC / g / pg['png']
                if src.exists():
                    shutil.copy2(src, outdir / pg['png'])
                    png_bytes_list.append(src.read_bytes())
        for src in sorted((SRC / g).glob('*.png')):
            if not (outdir / src.name).exists():
                shutil.copy2(src, outdir / src.name)
        lib = outdir / 'lib'
        lib.mkdir(exist_ok=True)
        for f in ('spine-player.js', 'spine-canvas.js'):
            sf = LIB / f
            if sf.exists() and not (lib / f).exists():
                shutil.copy2(sf, lib / f)
        anims = list(res['data'].get('animations', {}).keys())
        sk = res['data']['skeleton']
        w = sk['width'] or 400
        h = sk['height'] or 400
        pad = max(w, h, 100) * 0.15
        bounds = [sk['x'] - pad, sk['y'] - pad, w + pad * 2, h + pad * 2]
        write_preview(outdir, g, (outdir / (g + '.json')).read_bytes(),
                      (outdir / (g + '.atlas')).read_bytes(), png_bytes_list,
                      anims, res['version'], bounds)
        manifest.append({
            'name': g,
            'dir': g,
            'skeleton': g + '.json',
            'atlas': g + '.atlas',
            'version': res['version'],
            'animations': anims,
            'bones': len(res['data']['bones']),
            'slots': len(res['data']['slots']),
            'dup_regions': len(res['dup_regions']),
            'att_missing': len(res['att_missing']),
        })
        report['ok'].append(g)
        if res['dup_regions']:
            report['warn'].append((g, 'dup atlas regions: %d' % len(res['dup_regions'])))
    idx = {
        'schema_version': '1.0',
        'source': str(SRC),
        'converter': 'db2spine.py',
        'summary': {
            'groups': len(groups),
            'ok': len(report['ok']),
            'skipped': len(report['skipped']),
            'warnings': len(report['warn']),
        },
        'items': manifest,
    }
    (OUT / 'index.json').write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding='utf-8')
    print('OK:', len(report['ok']), 'skipped:', report['skipped'])
    print('warnings:', len(report['warn']))
    for w in report['warn'][:20]:
        print('  WARN', w)


if __name__ == '__main__':
    main()
