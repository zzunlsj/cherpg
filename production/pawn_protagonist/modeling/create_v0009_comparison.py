"""Produce REAL Blender-render comparison sheets for CheRPG v0.0.8 vs v0.0.9.
Does not create or enhance imagery: only tiles existing PNGs. Scientific review
aid, NOT automatic approval of model quality.
"""
import argparse,json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
p=argparse.ArgumentParser()
p.add_argument("--renders",required=True,type=Path)
p.add_argument("--out",required=True,type=Path)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
views=("front","profile","threequarter","face-detail","ear-detail")
results=[]
for view in views:
    src=[a.renders/f"pawn-head-shapes-v{version}-{view}.png" for version in ("0.0.8","0.0.9")]
    if not all(path.is_file() and path.stat().st_size>1000 for path in src):
        raise FileNotFoundError(f"Missing real Blender PNG(s): {src}")
    with Image.open(src[0]) as left, Image.open(src[1]) as right:
        if left.size!=right.size:raise ValueError(f"Mismatched render dimensions: {view}")
        w,h=left.size
        sheet=Image.new("RGB",(2*w,h+68),(245,245,245))
        sheet.paste(left.convert("RGB"),(0,68))
        sheet.paste(right.convert("RGB"),(w,68))
        d=ImageDraw.Draw(sheet)
        d.text((20,18),f"v0.0.8  |  {view}  (BEFORE)",fill=(20,20,20))
        d.text((w+20,18),f"v0.0.9  |  {view}  (AFTER)",fill=(20,20,20))
        target=a.out/f"pawn-head-v0008-v0009-{view}-comparison.png"
        sheet.save(target,optimize=True)
        results.append(target.name)
report={"from_version":"0.0.8","to_version":"0.0.9",
        "type":"unaltered adjacent render comparison",
        "review_status":"manual visual approval REQUIRED",
        "eye_policy":"no ocular objects; sculpt only",
        "sheets":results}
(a.out/"pawn-head-v0009-visual-review.json").write_text(
    json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
