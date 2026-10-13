"""CheRPG direction-device: standard-Python four-foot ground contact solver.
One unit = one meter, Z up; pawn faces -Y and does not rotate.
"""
from dataclasses import dataclass
import math

RING_RADIUS = 0.68
RING_Z = 0.748
ANCHOR_ANGLES = (45, 135, 225, 315)
FOOT_RADIUS = 0.075
FOOT_THICKNESS = 0.052
SPLIT_Z = 0.420
MIN_LOWER_STROKE = 0.18
MAX_LOWER_STROKE = 0.54
TILE_HALF = 1.0

@dataclass(frozen=True)
class Ground:
    slope_x: float = 0.0
    slope_y: float = 0.0
    bumps: tuple = ()

    def height(self, x, y):
        h = self.slope_x*x + self.slope_y*y
        for bx,by,amp,sigma in self.bumps:
            h += amp*math.exp(-((x-bx)**2 + (y-by)**2)/(2*sigma*sigma))
        return h

    def gradient(self, x, y):
        gx,gy = self.slope_x,self.slope_y
        for bx,by,amp,sigma in self.bumps:
            term=amp*math.exp(-((x-bx)**2+(y-by)**2)/(2*sigma*sigma))
            gx-=term*(x-bx)/sigma**2
            gy-=term*(y-by)/sigma**2
        return gx,gy

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(v,s): return tuple(x*s for x in v)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(v):
    norm=math.sqrt(dot(v,v))
    return tuple(x/norm for x in v)

def grounded_foot(ground, angle):
    rad=math.radians(angle)
    x,y=RING_RADIUS*math.cos(rad),RING_RADIUS*math.sin(rad)
    z=ground.height(x,y)
    gx,gy=ground.gradient(x,y)
    normal=unit((-gx,-gy,1.0))
    axis_u=unit((1.,0.,gx))
    axis_v=unit(cross(normal,axis_u))
    base=(x,y,z)
    tangent_samples=[]
    for frac in (0,.25,.5,.75,1.0):
        for i in range(128):
            a=math.tau*i/128
            tangent=add(mul(axis_u,frac*FOOT_RADIUS*math.cos(a)),
                        mul(axis_v,frac*FOOT_RADIUS*math.sin(a)))
            pt=add(base,tangent)
            tangent_samples.append((pt,ground.height(pt[0],pt[1])-pt[2]))
    corrective=max(delta for _,delta in tangent_samples)
    corrected_base=add(base,(0.,0.,max(0,corrective)))
    upper=add(corrected_base,mul(normal,FOOT_THICKNESS))
    stroke=SPLIT_Z-upper[2]
    samples=[corrected_base[2]+(p[2]-base[2])-ground.height(p[0],p[1])
             for p,_ in tangent_samples]
    min_gap=min(samples)
    max_gap=max(samples)
    within_tile=max(abs(x),abs(y))+FOOT_RADIUS<=TILE_HALF
    within_stroke=MIN_LOWER_STROKE<=stroke<=MAX_LOWER_STROKE
    body_clearance=math.hypot(x,y)-.29-.04
    return dict(angle=angle,x=x,y=y,terrain_z=z,
                base=corrected_base,upper=upper,normal=normal,
                lower_length=stroke,correction=max(0,corrective),
                minimum_gap_m=min_gap,maximum_gap_m=max_gap,
                within_stroke=within_stroke,within_tile=within_tile,
                body_clearance_m=body_clearance,
                safe=bool(within_tile and within_stroke and body_clearance>=.03 and min_gap>=-1e-7))

def solve(ground):
    feet=[grounded_foot(ground,a) for a in ANCHOR_ANGLES]
    return dict(safe=all(f['safe'] for f in feet),feet=feet,
                ring_edge_tile_clearance_m=TILE_HALF-RING_RADIUS-.024,
                height_range_m=max(f['terrain_z'] for f in feet)-min(f['terrain_z'] for f in feet))

PRESETS={
    'flat':Ground(),
    'slope_10deg_x':Ground(slope_x=math.tan(math.radians(10))),
    'slope_8deg_diagonal':Ground(slope_x=math.tan(math.radians(8))/math.sqrt(2),
                                   slope_y=math.tan(math.radians(8))/math.sqrt(2)),
    'micro_terrain':Ground(slope_x=.09,slope_y=-.045,
                     bumps=((.48,.48,.060,.31),(-.48,-.48,-.045,.28))),
    'too_steep_30deg':Ground(slope_x=math.tan(math.radians(30))),
}

if __name__=='__main__':
    import json
    for name,g in PRESETS.items():
        r=solve(g)
        print(name,'PASS' if r['safe'] else 'UNSUPPORTED',
              json.dumps({"height_range_m":round(r['height_range_m'],4),
                          "strokes":[round(f['lower_length'],3) for f in r['feet']],
                          "ground_gaps":[round(f['minimum_gap_m'],6) for f in r['feet']]}))
