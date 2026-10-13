"""Merge Blender 5.2.2 separate object actions into one glTF 2.0 animation."""
import copy
import json
import struct
from pathlib import Path

def merge_actions(source,destination,name="CheRPG_DeployGroundAndChangeHeading"):
    source,destination=Path(source),Path(destination)
    data=source.read_bytes()
    if data[:4]!=b"glTF" or struct.unpack_from("<I",data,4)[0]!=2 or struct.unpack_from("<I",data,8)[0]!=len(data):
        raise ValueError("Expected a valid GLB v2")
    pos=12
    chunks=[]
    while pos<len(data):
        size,kind=struct.unpack_from("<I4s",data,pos)
        pos+=8
        chunks.append((kind,data[pos:pos+size]))
        pos+=size
    if chunks[0][0]!=b"JSON":raise ValueError("Missing JSON chunk")
    gltf=json.loads(chunks[0][1])
    old=gltf.get("animations",[])
    if not old:raise ValueError("No animations to merge")
    merged={"name":name,"channels":[],"samplers":[]}
    targets=set()
    for anim in old:
        shift=len(merged["samplers"])
        merged["samplers"].extend(copy.deepcopy(anim["samplers"]))
        for ch in anim["channels"]:
            channel=copy.deepcopy(ch)
            channel["sampler"]+=shift
            target=channel["target"]
            identity=(target.get("node"),target.get("path"))
            if identity in targets:
                raise ValueError(f"Duplicate animation channel target: {identity}")
            targets.add(identity)
            merged["channels"].append(channel)
    gltf["animations"]=[merged]
    encoded=json.dumps(gltf,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    encoded+=b" "*((-len(encoded))%4)
    chunks[0]=(b"JSON",encoded)
    out=bytearray(struct.pack("<4sII",b"glTF",2,12+sum(8+len(part) for _,part in chunks)))
    for kind,chunk in chunks:
        out.extend(struct.pack("<I4s",len(chunk),kind))
        out.extend(chunk)
    destination.write_bytes(out)
    roundtrip=destination.read_bytes()
    decoded=json.loads(roundtrip[20:20+struct.unpack_from("<I",roundtrip,12)[0]])
    assert len(decoded["animations"])==1
    assert len(decoded["animations"][0]["channels"])==len(merged["channels"])
    return {"original_clips":len(old),"unified_clips":1,"channels":len(merged["channels"]),"output":destination.name}
