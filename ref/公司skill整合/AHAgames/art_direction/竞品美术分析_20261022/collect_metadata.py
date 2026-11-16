from pathlib import Path
import urllib.request,urllib.parse,json,concurrent.futures
ROOT=Path(__file__).parent
GAMES=[('block_blast','Block Blast'),('pizza_ready','Pizza Ready'),('ludo_king','Ludo King'),('subway_surfers','Subway Surfers'),('tile_explorer','Tile Explorer Triple Match'),('mob_control','Mob Control'),('block_out','Block Out Color Sort Puzzle'),('magic_sort','Magic Sort Grand Games'),('meowdoku','Meowdoku'),('arrows_escape','Arrows Puzzle Escape'),('arrows_go','Arrows GO'),('awesome_games','Awesome Games Offline Arcade'),('brain_puzzle_3','Brain Puzzle 3 Crazy Mind'),('offline_games','Offline Games No Wifi JindoBlu'),('candy_crush','Candy Crush Saga'),('perfect_makeover','Perfect Makeover Cleaning ASMR'),('bus_fever','Bus Fever Party'),('muscle_morph','Muscle Morph'),('talking_tom_2','My Talking Tom 2')]
def collect(item):
 key,term=item
 p=ROOT/f'{key}_search.json'
 if p.exists():return key,json.loads(p.read_text(encoding='utf-8'))
 url='https://itunes.apple.com/search?'+urllib.parse.urlencode(dict(term=term,entity='software',country='us',limit=12))
 try:
  with urllib.request.urlopen(url,timeout=35) as r:data=json.load(r)
  p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
  return key,data
 except Exception as e:return key,{'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for key,data in pool.map(collect,GAMES):
  print(key, json.dumps([{'id':x.get('trackId'),'name':x.get('trackName'),'seller':x.get('sellerName'),'url':x.get('trackViewUrl'),'screens':len(x.get('screenshotUrls',[]))} for x in data.get('results',[])][:7],ensure_ascii=False) if 'error' not in data else data)
