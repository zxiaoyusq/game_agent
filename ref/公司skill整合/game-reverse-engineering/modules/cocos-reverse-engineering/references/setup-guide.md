# Setup Guide: Dependencies for Cocos Creator Reverse Engineering
> **何时读我**：要装或查本机逆向工具环境（Node.js、`cc-reverse` 本体、解压/音视频/jq 等可选工具），或依赖相关报错（找不到 node / cc-reverse / xxtea-node、项目检测失败）要排查时。
> **读完能做到**：在 Ubuntu/Fedora/Arch/macOS 或无 sudo 的环境下把依赖装齐并验证，从 APK 中取出 Cocos 游戏数据，并按故障表解决常见的安装与检测问题。
> **范围**：`GENERAL_DEFAULT`

## Node.js 16+

`cc-reverse` needs Node.js (it uses `@babel/parser` for script recovery and a few modern stdlib APIs).

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y nodejs npm
# Or pin a newer version with nodesource:
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt install -y nodejs
```

### Fedora

```bash
sudo dnf install -y nodejs npm
```

### Arch Linux

```bash
sudo pacman -S --noconfirm nodejs npm
```

### macOS (Homebrew)

```bash
brew install node
```

### Without sudo (any OS)

Use [nvm](https://github.com/nvm-sh/nvm):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
# Restart shell, then:
nvm install 20
nvm use 20
```

### Verify

```bash
node --version   # v16.x or newer
npm --version
```

---

## cc-reverse

The reverse engineering engine this skill wraps.

### From npm (recommended)

```bash
npm install -g cc-reverse
```

If you get `EACCES` on Linux, configure npm to install into your home directory (no sudo):

```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=$HOME/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
npm install -g cc-reverse
```

### From source

```bash
git clone https://github.com/Crain99/cc-reverse.git
cd cc-reverse
npm install
export CC_REVERSE_HOME=$(pwd)
# Then run: node bin/cc-reverse.js --help
```

The skill scripts pick up `$CC_REVERSE_HOME` automatically if `cc-reverse` is not on `PATH`.

### Verify

```bash
cc-reverse --help
```

---

## Archive tools (optional)

Compiled game builds often ship as ZIPs (or inside APKs).

### unzip

```bash
# Ubuntu/Debian
sudo apt install -y unzip
# Fedora
sudo dnf install -y unzip
# macOS (bundled)
```

### 7z (p7zip)

```bash
# Ubuntu/Debian
sudo apt install -y p7zip-full
# Fedora
sudo dnf install -y p7zip
# macOS
brew install p7zip
```

### Extracting a Cocos game from an APK

```bash
# APK is just a ZIP. The Cocos game data lives under assets/ inside it.
unzip -q my-game.apk -d my-game-apk
# Cocos 3.x native: assets/jsb-adapter/, data/, src/cocos-js/
# Cocos 2.x native: assets/res/, assets/src/, assets/main.js
# Point the detector at the `assets/` directory inside the APK.
```

---

## ffmpeg (optional)

Useful if the game ships audio in a format your target platform dislikes. `cc-reverse` preserves whatever format the build shipped (mp3/ogg/wav/m4a); use ffmpeg to re-encode if needed.

```bash
# Ubuntu/Debian
sudo apt install -y ffmpeg
# Fedora
sudo dnf install -y ffmpeg
# macOS
brew install ffmpeg
```

---

## jq (optional)

3.x builds stash important config in `src/settings.json` and per-bundle `config.json`. `jq` makes quick inspection easier.

```bash
# Ubuntu/Debian
sudo apt install -y jq
# Fedora
sudo dnf install -y jq
# macOS
brew install jq

# Show all bundle names
jq -r '.assets.bundleVers | keys[]' src/settings.*.json
# Show class-id list for a bundle
jq '.types' assets/main/config.json
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `node: command not found` | Node isn't on PATH. With nvm: `nvm use 20`. With system install: verify `/usr/bin/node` exists. |
| `cc-reverse: command not found` after `npm install -g` | npm's global bin dir isn't on PATH. Run `npm config get prefix`; add `$(npm config get prefix)/bin` to `$PATH`. |
| `Error: Cannot find module 'xxtea-node'` | Reinstall: `cd $(npm root -g)/cc-reverse && npm install`. |
| Detection fails on an obvious Cocos build | The root you pointed at probably has a parent/child layer. Run `detect-project.sh` against both the parent and child directories. |
| `无法检测到有效的Cocos Creator项目结构` | Pass `--version-hint 2.4.x` (or `3.x`). If still failing, the build may use a custom packing plugin — read `cocos3x-format.md` for known variants. |
| `.jsc` files persist in the output | The XXTEA key was wrong or not found. Re-run `find-jsc-key.sh`; if nothing comes back, ask the developer for the key. |
| 3.x `config.json` has `encrypted: true` but `cc-reverse` reports no `.jsc` found | The bundle index file is named `index.[ver].jsc`; make sure the detector is scanning recursively (it does by default). |
