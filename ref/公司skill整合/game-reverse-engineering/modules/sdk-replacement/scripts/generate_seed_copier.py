#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate an offline Seed copier by merging v8.5 interfaces and local safeguards.

Java: --roots selects subdirectories; --target-subdir seed preserves local legacy
layout, while --target-subdir . writes directly into filesDir. Supports custom
class/package, --check and --emit-usage. --language smali emits an explicitly
incomplete integration skeleton, never a working copier. Desktop stub tests
verify generated Java; real Android offline startup still requires device QA.
"""
from pathlib import Path
import argparse, json, re, sys

TEMPLATE = r'''package {java_package};

import android.content.Context;
import android.content.res.AssetManager;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * 自动生成：game-reverse-engineering / modules/sdk-replacement / scripts/generate_seed_copier.py
 *
 * 调用点：Application.onCreate() 的 super.onCreate() 之后、任何 SDK/壳初始化之前。
 * 幂等：{marker} 存在即跳过。
 */
public final class {class_name} {{

    private static final String TAG = "{log_tag}";
    /** APK assets 内的 Seed 根目录（相对 assets/）。 */
    private static final String ASSET_ROOT = "{asset_dir}";
    /** 落地到 filesDir 下的子目录。 */
    private static final String TARGET_SUBDIR = "{target_subdir}";
    /** 完成标记文件名。 */
    private static final String MARKER = "{marker}";
    private static final String[] ROOTS = new String[] {{{roots}}};
    private static final int BUFFER_SIZE = 1 << 16;

    private final Context context;
    public {class_name}(Context context) {{ this.context = context.getApplicationContext(); }}
    public void copySync() {{ copyIfNeeded(context); }}
    public void copyAsync() {{
        new Thread(new Runnable() {{
            @Override public void run() {{ copyIfNeeded(context); }}
        }}, "{class_name}-copy").start();
    }}

    public static void copyIfNeeded(Context context) {{
        final long startedAt = System.currentTimeMillis();
        try {{
            File targetRoot = new File(context.getFilesDir(), TARGET_SUBDIR);
            File marker = new File(targetRoot, MARKER);
            if (marker.isFile()) {{
                Log.i(TAG, "seed already materialized, skip");
                return;
            }}
            if (!targetRoot.exists() && !targetRoot.mkdirs()) {{
                Log.w(TAG, "cannot create target dir: " + targetRoot);
                return;
            }}
            AssetManager assets = context.getAssets();
            Stats stats = new Stats();
            if (ROOTS.length == 0) {{
                copyTree(assets, ASSET_ROOT, targetRoot, stats);
            }} else {{
                for (String root : ROOTS) {{
                    copyTree(assets, ASSET_ROOT + "/" + root, new File(targetRoot, root), stats);
                }}
            }}
            if (!stats.failed()) {{
                writeMarker(marker, stats);
                Log.i(TAG, "seed materialized files=" + stats.copied + " skipped=" + stats.skipped
                        + " cost=" + (System.currentTimeMillis() - startedAt) + "ms");
            }} else {{
                Log.w(TAG, "seed incomplete, marker NOT written: failed=" + stats.failed);
            }}
        }} catch (Throwable t) {{
            Log.e(TAG, "seed copy failed", t);
        }}
    }}

    private static void copyTree(AssetManager assets, String assetPath, File targetDir, Stats stats) {{
        String[] children;
        try {{
            children = assets.list(assetPath);
        }} catch (IOException e) {{
            stats.failed++;
            Log.w(TAG, "list failed: " + assetPath, e);
            return;
        }}
        if (children == null || children.length == 0) {{
            copyFile(assets, assetPath, targetDir, stats);
            return;
        }}
        if (!targetDir.exists() && !targetDir.mkdirs()) {{
            stats.failed++;
            return;
        }}
        for (String child : children) {{
            copyTree(assets, assetPath + "/" + child, new File(targetDir, child), stats);
        }}
    }}

    private static void copyFile(AssetManager assets, String assetPath, File target, Stats stats) {{
        File tmp = new File(target.getPath() + ".seedtmp");
        try (InputStream in = assets.open(assetPath, AssetManager.ACCESS_STREAMING)) {{
            long expected = in.available(); // Retry optimization only; final Seed acceptance uses hashes.
            if (target.isFile() && expected > 0 && target.length() == expected) {{
                stats.skipped++;
                return;
            }}
            File parent = target.getParentFile();
            if (parent != null && !parent.exists() && !parent.mkdirs()) {{
                throw new IOException("cannot create target parent");
            }}
            try (OutputStream out = new FileOutputStream(tmp)) {{
                byte[] buffer = new byte[BUFFER_SIZE];
                int count;
                while ((count = in.read(buffer)) != -1) {{
                    out.write(buffer, 0, count);
                }}
                out.flush();
            }}
            if (target.exists() && !target.delete()) throw new IOException("cannot replace target");
            if (!tmp.renameTo(target)) throw new IOException("cannot commit target");
            stats.copied++;
        }} catch (Throwable t) {{
            stats.failed++;
            tmp.delete();
            Log.w(TAG, "copy failed: " + assetPath, t);
        }}
    }}

    private static void writeMarker(File marker, Stats stats) {{
        File tmp = new File(marker.getParentFile(), marker.getName() + ".tmp");
        OutputStream out = null;
        try {{
            out = new FileOutputStream(tmp);
            out.write(("copied=" + stats.copied + "\nskipped=" + stats.skipped + "\n").getBytes("UTF-8"));
            out.flush();
        }} catch (Throwable t) {{
            Log.w(TAG, "write marker tmp failed", t);
            return;
        }} finally {{
            closeQuietly(out);
        }}
        if (!tmp.renameTo(marker)) {{
            tmp.delete();
            Log.w(TAG, "marker commit failed; next launch must retry");
        }}
    }}

    private static String baseName(String path) {{
        int idx = path.lastIndexOf('/');
        return idx >= 0 ? path.substring(idx + 1) : path;
    }}

    private static void closeQuietly(java.io.Closeable closeable) {{
        if (closeable == null) return;
        try {{
            closeable.close();
        }} catch (Throwable ignored) {{
        }}
    }}

    private static final class Stats {{
        int copied;
        int skipped;
        int failed;

        boolean failed() {{
            return failed > 0;
        }}
    }}
}}
'''

USAGE = '''# SeedCopier 接入片段（自动生成）

## 1. Java：Application.onCreate()

```java
@Override
public void onCreate() {
    super.onCreate();

    // 1) 先固化 Seed（幂等）
    %CLASS%.copyIfNeeded(this);

    // 2) 之后才是壳 / SDK / 新供应商初始化
    // ... your sdk init ...
}
```

## 2. smali（若走 apktool 路线）

在 Application 子类的 onCreate() 中、invoke-super 之后插入：

```smali
    invoke-static {p0}, L%PKGPATH%/%CLASS%;->copyIfNeeded(Landroid/content/Context;)V
```

## 3. 校验要点

- 首次启动后检查 filesDir/%SUBDIR%/%MARKER% 是否存在；
- 断网冷启动 3 次，均能进入可玩场景；
- 目录大小一致 **不等于** 完整：用 prepare_offline_seed.py --check-only 做文件级/哈希级门禁。
'''

def java_text(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]

def normalized_path(raw, allow_dot=False):
    raw = raw.replace('\\', '/').strip()
    if allow_dot and raw in ('', '.'):
        return ''
    if raw.startswith('/') or ':' in raw:
        raise ValueError('paths must be relative')
    parts = raw.strip('/').split('/')
    if not parts or any(p in ('', '.', '..') for p in parts):
        raise ValueError('empty, dot and traversal path components are not allowed')
    return '/'.join(parts)

def main():
    ap = argparse.ArgumentParser(description='Generate a Java Seed copier or an incomplete Smali integration skeleton')
    ap.add_argument('--package', required=True)
    ap.add_argument('--asset-dir', default='assets/remote_seed')
    ap.add_argument('--marker', default='.seed_done')
    ap.add_argument('--roots', default='', help='Comma separated relative roots; default copies the whole seed tree')
    ap.add_argument('--language', choices=['java', 'smali'], default='java')
    ap.add_argument('--target-subdir', default='seed', help='filesDir subdirectory; . means filesDir itself')
    ap.add_argument('--class-name', default='SeedCopier')
    ap.add_argument('--java-package', default='')
    ap.add_argument('--log-tag', default='SeedCopier')
    ap.add_argument('--out', default='SeedCopier.java')
    ap.add_argument('--emit-usage', default='')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    try:
        pkg = args.java_package or args.package
        reserved = set('abstract assert boolean break byte case catch char class const continue default do double else enum extends final finally float for goto if implements import instanceof int interface long native new package private protected public return short static strictfp super switch synchronized this throw throws transient try void volatile while true false null _ var yield record sealed permits'.split())
        identifiers = pkg.split('.') + [args.class_name]
        if any(not re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', part) or part in reserved for part in identifiers):
            raise ValueError('invalid Java package or class identifier')
        asset = args.asset_dir.replace('\\', '/')
        if asset.startswith('assets/'):
            asset = asset[len('assets/'):]
        asset = normalized_path(asset)
        target = normalized_path(args.target_subdir, allow_dot=True)
        roots = [normalized_path(p.strip()) for p in args.roots.split(',') if p.strip()]
        if len(set(roots)) != len(roots):
            raise ValueError('duplicate roots')
        if any(a.startswith(b + '/') for a in roots for b in roots if a != b):
            raise ValueError('overlapping roots')
        marker = args.marker
        if marker in ('', '.', '..') or any(c in marker for c in '/\\\n\r"'):
            raise ValueError('marker must be a single file name')
    except ValueError as exc:
        ap.error(str(exc))
    if args.language == 'java':
        rendered = TEMPLATE.format(java_package=pkg, class_name=args.class_name,
            asset_dir=java_text(asset), target_subdir=java_text(target), marker=java_text(marker),
            log_tag=java_text(args.log_tag), roots=', '.join(json.dumps(p) for p in roots))
    else:
        rendered = f"""# INCOMPLETE: integration skeleton only; compile the Java copier to DEX for real use.
.class public L{pkg.replace('.', '/')}/{args.class_name};
.super Ljava/lang/Object;
.method public static copyIfNeeded(Landroid/content/Context;)V
    .locals 0
    # TODO: seed copying is not implemented in this skeleton.
    return-void
.end method
"""
    usage = (USAGE.replace('%CLASS%', args.class_name).replace('%PKGPATH%', pkg.replace('.', '/'))
                  .replace('%SUBDIR%', target or '.').replace('%MARKER%', marker))
    if args.check:
        print('PASS: arguments validated and template rendered; no files written')
        return 0
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding='utf-8', newline='\n')
    if args.emit_usage:
        dest = Path(args.emit_usage); dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(usage, encoding='utf-8', newline='\n')
    print(json.dumps({'out': str(out), 'language': args.language, 'package': pkg,
        'asset_dir': asset, 'target_subdir': target, 'roots': roots,
        'state': 'JAVA_GENERATED' if args.language == 'java' else 'INCOMPLETE_SMALI_SKELETON'}, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    sys.exit(main())
