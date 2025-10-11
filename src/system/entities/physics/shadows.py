import math
import pygame
import numpy as np
import pygame.gfxdraw as gfx
from dataclasses import dataclass
from typing import Optional, List, Tuple
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj

@dataclass
class EllipseData:
    center: Coord
    rx: float
    ry: float
    rotation: float

@dataclass
class Receiver:
    # Plane: n·X + d = 0  (n is NOT required to be unit length here)
    n: Coord 
    d: float
    # Top-down footprint of this surface (convex, CCW) in world XY
    polygon: list[Coord]
    # A hint for sorting “higher first” (max z over footprint vertices)
    ref_z: float
    min_z: float
    id: int | None = None
    shade_level: ShadeLevel = ShadeLevel.CANOPY_START

    def z_at(self, x: float, y: float) -> float:
        # Solve n.x*x + n.y*y + n.z*z + d = 0  =>  z = -(d + n.x*x + n.y*y)/n.z
        if abs(self.n.z) < 1e-8:
            raise ValueError("Normal z must be greater than 0")
        return (-(self.d + self.n.x*x + self.n.y*y) / self.n.z)

    def project_xy_to_world(self, x: float, y: float) -> Coord:
        z = self.z_at(x, y)
        return Coord.math(x, y, z)

    @staticmethod
    def from_horizontal(polygon: List[Coord]):
        # For z = const, plane is n=(0,0,1), d=-z (or any scalar multiple)
        n = Coord.math(0, 0, 1)
        z = polygon[0].z
        return Receiver(n=n, d=-z, polygon=polygon, ref_z=z, min_z=z)

    @staticmethod
    def from_triangle(polygon: List[Coord]):
        p0, p1, p2 = polygon
        n = (p1 - p0).cross(p2 - p0)
        if n.norm() == 0:
            raise ValueError("Degenerate triangle")
        
        # Use point p0 to solve for d: n·X + d = 0  => d = -n·p0
        d = -n.dot(p0)
        polygon = [Coord.math(p0.x, p0.y, 0), Coord.math(p1.x, p1.y, 0), Coord.math(p2.x, p2.y, 0)]
        ref_z = max(p0.z, p1.z, p2.z)
        min_z = min(p0.z, p1.z, p2.z)
        return Receiver(n=n, d=d, polygon=polygon, ref_z=ref_z, min_z=min_z)
    
    @staticmethod
    def load_receiver(polygon: List[Coord], shade_level: ShadeLevel):
        r = Receiver.from_triangle(polygon) if len(polygon) == 3 else Receiver.from_horizontal(polygon)
        r.shade_level = shade_level
        return r


class Shadows:
    """ Builds a 3D world representation to cast noon shadows onto reciever surfaces"""
    STRICT = True

    def __init__(self, ellipse_samples: int = 16):
        self.receivers = []
        self.ellipse_samples = ellipse_samples

    def add_receiver(self, polygon: List[Coord], shade_level: ShadeLevel) -> None:
        """ Adds a triangle or horizonatal plane to receivers """
        self.receivers.append(Receiver.load_receiver(polygon, shade_level))

    def reset_receivers(self) -> None:
        self.receivers = []

    def update(self) -> None:
        self.receivers.sort(key=lambda r: r.ref_z, reverse=True)

    def get_shadow_objs(self, ellipse: EllipseData) -> List[RenderObj]:
        render_obs: List[RenderObj] = []

        higher = []
        self.receivers.sort(key=lambda r: r.ref_z, reverse=True)
        ellipse_poly = self.generate_ellipse_poly(ellipse, samples=self.ellipse_samples)
        ellipse_bbox  = self._bbox_xy(ellipse_poly)
        

        for reciever in self.receivers:

            # Quick checks to discount recievers 
            if reciever.min_z >= ellipse.center.z: continue
            if not self._bbox_overlaps(ellipse_bbox, self._bbox_xy(reciever.polygon), pad=1e-6): continue

            # Base region on this receiver
            region_in_shadow = self.poly_intersection(ellipse_poly, reciever.polygon)
            if len(region_in_shadow) < 3: continue

            # Decide which higher receivers actually steal rays here and collect 'holes'
            hole_polys_xy = []
            for higher_reciever in higher:
                overlap = self.poly_intersection(region_in_shadow, higher_reciever.polygon)
                if (centriod := self.poly_centroid(overlap)):
                    reciever_hieght = reciever.z_at(centriod.x, centriod.y)
                    higher_reciver_hieght = higher_reciever.z_at(centriod.x, centriod.y)

                    # double check the higher z > reciever z and add it holes
                    if (higher_reciver_hieght < ellipse.center.z) and (higher_reciver_hieght > reciever_hieght + 1e-4):
                        hole_polys_xy.append(overlap)

            # reciever truly receives shadow so it can occlude things below
            higher.append(reciever)

            # Project base + holes to screen using this receiver’s plane
            base_screen = []
            holes_screen = []
            min_x = min_y = float("inf")
            max_x = max_y = float("-inf")

            # Construct shadow poly in view coords that hits reciever
            for point in region_in_shadow:
                point_3d = reciever.project_xy_to_world(point.x, point.y)
                point_3d.z = min(point_3d.z, ellipse.center.z)
                px, py = point_3d.as_view_coord()
                base_screen.append((px, py))
                min_x, max_x, min_y, max_y = min(min_x, px), max(max_x, px), min(min_y, py), max(max_y, py)

            # Construct polys to remove from reciever shadow poly in view coords
            for hole_xy in hole_polys_xy:
                holes = []
                for point in hole_xy:
                    point_3d = reciever.project_xy_to_world(point.x, point.y)
                    point_3d.z = min(point_3d.z, ellipse.center.z)
                    px, py = point_3d.as_view_coord()
                    holes.append((px, py))
                    min_x, max_x, min_y, max_y = min(min_x, px), max(max_x, px), min(min_y, py), max(max_y, py)
                holes_screen.append(holes)


            if not base_screen: continue

            # Alpha & softness from height
            centriod = self.poly_centroid(region_in_shadow)
            reciever_centriod_height = reciever.z_at(centriod.x, centriod.y)
            hgap = max(0.0, ellipse.center.z - reciever_centriod_height)
            alpha = self.get_alpha(hgap)


            # Build tight surface
            pad = 1.0
            s_w = max(1, int(math.ceil(max_x - min_x))) + 2 * pad
            s_h = max(1, int(math.ceil(max_y - min_y))) + 2 * pad
            offset_x, offset_y = int(math.floor(min_x)) - pad, int(math.floor(min_y)) - pad

            # Base fill
            shadow_surf = pygame.Surface((s_w, s_h), pygame.SRCALPHA)
            pygame.draw.polygon(shadow_surf, (0, 0, 0, alpha), self._get_local_poly(offset_x, offset_y, base_screen))

            # Single occluder mask to punch holes 
            if holes_screen:
                occ = pygame.Surface((s_w, s_h), pygame.SRCALPHA)
                for hole in holes_screen:
                    pygame.draw.polygon(occ, (0, 0, 0, 255), self._get_local_poly(offset_x, offset_y, hole))
                
                occ = self._blur_surface(occ, passes=1)
                shadow_surf.blit(occ, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            render_obs.append(
                RenderObj(
                    None,
                    np.array([min_x, min_y]),
                    (reciever.shade_level, centriod.x if centriod else 0.0, centriod.y if centriod else 0.0, reciever.ref_z),
                    isShadow=True,
                    img=shadow_surf,
                )
            )

        return render_obs
    

    @staticmethod
    def _get_local_poly(offset_x: int, offset_y: int, poly: List[Coord]) -> List[Coord]:
        return [(int(round(x - offset_x)), int(round(y - offset_y))) for (x, y) in poly]


    @staticmethod
    def get_alpha(height: float) -> int:
        t = max(0.0, min(1.0, height / 8.0))
        return int(120 * (1.0 - t) + 50 * t)

    @staticmethod
    def side(p: Coord, a: Coord, b: Coord) -> float:
        """Signed area test: >0 = p is left of CCW edge a->b; <0 = right; 0 = colinear."""
        return (b - a).cross_2D(p - a)

    @staticmethod
    def intersect(p1: Coord, p2: Coord, a: Coord, b: Coord) -> Coord:
        """
        Intersection of segment p1->p2 with the infinite line through edge a->b.
        Returns a point with z=0 (XY-only; the true z will be computed later).
        """
        r, s = p2 - p1, b - a
        denom = r.cross_2D(s)
        if abs(denom) < 1e-8:
            return Coord.math(p1.x, p1.y, 0)
        t = (a - p1).cross_2D(s) / denom
        return Coord.math(p1.x + r.x * t, p1.y + r.y * t, 0)

    @staticmethod
    def poly_intersection(subject: List[Coord], clipper: List[Coord]) -> List[Coord]:
        """ CCW polygon of subject ∩ clipper (clipper must be convex & CCW). """

        out = subject[:]
        for i in range(len(clipper)):
            a, b = clipper[i], clipper[(i + 1) % len(clipper)]
            inp, out = out, []

            if not inp:
                break

            prev = inp[-1]
            prev_in = Shadows.side(prev, a, b) >= -1e-8

            for cur in inp:
                cur_in = Shadows.side(cur, a, b) >= -1e-8

                if cur_in:
                    if not prev_in:
                        out.append(Shadows.intersect(prev, cur, a, b))
                    out.append(cur)
                else:
                    if prev_in:
                        out.append(Shadows.intersect(prev, cur, a, b))

                prev, prev_in = cur, cur_in

        return out


    @staticmethod
    def generate_ellipse_poly(
        ellipse_data: EllipseData,
        samples: int = 48,
    ) -> List[Coord]:
        """
        Sample points on an ellipse centered at (cx, cy), with radii (rx, ry),
        optionally rotated by angle_rad about the z-axis (i.e., in the XY plane).

        The parameterization is t in [0, 2π). For angle_rad = 0, the major/minor
        axes align with +x / +y. For angle_rad > 0, the ellipse is rotated CCW.
        """

        rx, ry = ellipse_data.rx, ellipse_data.ry
        cx, cy, height = ellipse_data.center.location

        ct = math.cos(ellipse_data.rotation)
        st = math.sin(ellipse_data.rotation)
        pts: List[Coord] = []

        for i in range(samples):
            t = 2.0 * math.pi * i / samples
            c = math.cos(t)
            s = math.sin(t)

            # local (unrotated) ellipse point
            ex = rx * c
            ey = ry * s

            # rotate and translate
            x = cx + ex * ct - ey * st
            y = cy + ex * st + ey * ct
            pts.append(Coord.math(x, y, height))

        if Shadows.STRICT: Shadows._ensure_ccw(pts)
        
        return pts

    @staticmethod
    def poly_centroid(poly: List[Coord]) -> Optional[Coord]:
        """ Computes rough 2D centriod """
        if len(poly) < 3: return None
        sx = sy = 0
        for p in poly:
            sx += p.x
            sy += p.y

        return Coord.math(sx / len(poly), sy / len(poly), 0)
    
    @staticmethod
    def _signed_area_ccw(poly: List[Coord]) -> float:
        a = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i].x, poly[i].y
            x2, y2 = poly[(i+1) % len(poly)].x, poly[(i+1) % len(poly)].y
            a += x1 * y2 - x2 * y1
        return 0.5 * a

    @staticmethod
    def _ensure_ccw(poly: List[Coord]) -> List[Coord]:
        return poly if Shadows._signed_area_ccw(poly) > 0 else list(reversed(poly))
    
    @staticmethod
    def _bbox_xy(poly: List[Coord]) -> Tuple[float,float,float,float]:
        """(min_x, min_y, max_x, max_y) in world XY."""
        xs = [p.x for p in poly]; ys = [p.y for p in poly]
        return (min(xs), min(ys), max(xs), max(ys))

    @staticmethod
    def _bbox_overlaps(a: Tuple[float,float,float,float],
                    b: Tuple[float,float,float,float],
                    pad: float = 0.0) -> bool:
        """True if AABBs overlap (optionally grown by `pad`)."""
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ax1 -= pad; ay1 -= pad; ax2 += pad; ay2 += pad
        bx1 -= pad; by1 -= pad; bx2 += pad; by2 += pad
        return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)
    
    @staticmethod
    def _blur_surface(src: pygame.Surface, passes: int = 1) -> pygame.Surface:
        """Fast, cheap blur: downsample then upsample (repeat)."""
        if passes <= 0:
            return src
        w, h = src.get_size()
        out = src.copy()
        for _ in range(passes):
            dw = max(1, int(w * 0.5))
            dh = max(1, int(h * 0.5))
            out = pygame.transform.smoothscale(out, (dw, dh))
            out = pygame.transform.smoothscale(out, (w,  h))
        return out
