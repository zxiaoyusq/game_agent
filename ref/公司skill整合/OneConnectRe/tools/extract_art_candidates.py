from pathlib import Path
import csv,colorsys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
root=Path(__file__).resolve().parent.parent;work=root/'美术换皮准备/20261029_四主题换皮';out=work/'候选逐帧';out.mkdir(exist_ok=False)
source=list(csv.DictReader((work/'原牌色彩映射_待核对.csv').open(encoding='utf-8-sig')));font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
reports=[]
def runs(mask):
 a=np.flatnonzero(mask);result=[]
 if not len(a):return result
 start=prev=int(a[0])
 for x in a[1:]:
  x=int(x)
  if x>prev+1:result.append((start,prev));start=x
  prev=x
 result.append((start,prev));return [x for x in result if x[1]-x[0]>180]
def dominant(im):
 rgb=np.array(im.convert('RGB'));rgba=np.array(im.convert('RGBA'));hsv=np.array(im.convert('RGB').convert('HSV'));h,s,v=hsv[:,:,0],hsv[:,:,1],hsv[:,:,2];mask=(rgba[:,:,3]>220)&(s>80)&(v>55)
 if not mask.any():return None
 ix=int(np.bincount((h[mask].astype(int)*24)//256,minlength=24).argmax());sel=mask&((h.astype(int)*24)//256==ix);med=np.median(rgb[sel],axis=0).astype(int);return {'hex':'#%02X%02X%02X'%tuple(med),'hue':(ix+.5)*15}
for theme in ['动物','甜点','水果','斋月']:
 f=work/(theme+'_按原色_候选.png');im=Image.open(f).convert('RGBA');alpha=np.array(im)[:,:,3];xs=runs((alpha>200).sum(axis=0)>60);ys=runs((alpha>200).sum(axis=1)>60)
 if len(xs)!=5 or len(ys)!=4:raise ValueError(f'{theme} grid detection failed x={xs} y={ys}')
 # A small symmetric margin retains antialiased card edges and limits gutter artifacts.
 sheet=Image.new('RGB',(1000,4*150),'#263248');draw=ImageDraw.Draw(sheet)
 for i in range(20):
  col,row=i%5,i//5;x0,x1=xs[col];y0,y1=ys[row];pad=3;crop=im.crop((max(0,x0-pad),max(0,y0-pad),min(im.width,x1+pad+1),min(im.height,y1+pad+1)))
  scaled=ImageOps.contain(crop,(94,94),Image.Resampling.LANCZOS);tile=Image.new('RGBA',(96,96),(0,0,0,0));tile.paste(scaled,((96-scaled.width)//2,(96-scaled.height)//2));tile.save(out/f'{theme}_{i+1:02}.png')
  original=next((a for a in source if a['theme']==(theme if theme!='斋月' else '动物') and int(a['frame'])==i+1),None);color=dominant(tile);hue0=float(original['hue_degrees_approx']);diff=None if not color or hue0<0 else min(abs(hue0-color['hue']),360-abs(hue0-color['hue']))
  reports.append({'theme':theme,'frame':i+1,'old_color':original['candidate_main_color'],'new_color':color['hex'] if color else '', 'hue_diff':diff,'status':'需人工核对' if diff is None or diff>30 or theme=='斋月' else '待视觉核验', 'old_theme':'动物（临时参考）' if theme=='斋月' else theme})
  x=col*200;y=row*150;old=Image.open(work/'原版牌面参考'/original['source_icon']).convert('RGBA');sheet.paste(old,(x,y+15),old);sheet.paste(tile,(x+100,y+15),tile);draw.text((x+5,y+115),f'{theme} {i+1:02}  旧 → 新',font=font,fill='white');draw.text((x+5,y+132),f"{original['candidate_main_color']} → {color['hex'] if color else '无'}",font=font,fill='white')
 sheet.save(work/(theme+'_原版与候选_96px.png'))
with (work/'候选颜色检查.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=reports[0]);writer.writeheader();writer.writerows(reports)
print('extracted',len(reports),'needs review',sum(x['status']=='需人工核对' for x in reports));print('per theme', {t:sum(r['status']=='需人工核对' for r in reports if r['theme']==t) for t in ['动物','甜点','水果','斋月']})
