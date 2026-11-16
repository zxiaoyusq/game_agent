import unittest,tempfile,importlib.util
from pathlib import Path
from PIL import Image
p=Path('tools/art_atlas_pack.py'); spec=importlib.util.spec_from_file_location('art_atlas_pack',p) if p.exists() else None
class ArtPack(unittest.TestCase):
 def test_frame_replacement_keeps_unrelated_pixels_and_missing_fails(self):
  self.assertTrue(p.exists(),'atlas packer not yet implemented')
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);base=d/'base';icons=d/'icons';out=d/'out';base.mkdir();icons.mkdir();Image.new('RGBA',(12,8),(12,14,16,255)).save(base/'sheet.png');Image.new('RGBA',(3,3),(255,0,0,255)).save(icons/'a.png')
   rows=[{'atlas':'sheet.png','x':1,'y':1,'width':3,'height':3,'icon':'a.png'},{'atlas':'sheet.png','x':6,'y':1,'width':3,'height':3,'icon':'b.png'}]
   with self.assertRaises(ValueError):m.pack_atlases(base,icons,out,rows)
   self.assertFalse(out.exists())
   Image.new('RGBA',(3,3),(0,0,255,255)).save(icons/'b.png');m.pack_atlases(base,icons,out,rows)
   im=Image.open(out/'sheet.png').convert('RGBA');self.assertEqual(im.getpixel((2,2)),(255,0,0,255));self.assertEqual(im.getpixel((7,2)),(0,0,255,255));self.assertEqual(im.getpixel((11,7)),(12,14,16,255))
if __name__=='__main__':unittest.main()
