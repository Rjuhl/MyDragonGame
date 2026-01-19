import math
import pygame
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple

from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel
from system.render_obj import RenderObj


# Move shadow lower to make it clear it is below caster
SHADOW_CLAMP = 0.5


# -----------------------------------------------------------------------------
# Geometry data
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class EllipseData:
    """
        Defines the (world-space) ellipse used as the "shadow footprint" for a caster.

        center: world-space center of ellipse (x, y, z)
        rx, ry: radii in world units
        rotation: rotation in radians (CCW in XY plane)
    """
    center: Coord
    rx: float
    ry: float
    rotation: float


class Triangle:
    """
        Represents a plane in 3D space bounded by a triangle.

        This is used to:
        - test whether an (x,y) lies inside the triangle's 2D projection
        - compute the corresponding z on the plane for that (x,y)
    """
    def __init__(self, points = List[Coord]):
        if len(points) != 3: raise ValueError("Triangle can only be initlized with 3 points")

        self.p0, self.p1, self.p2 = points
        self.n = (self.p1 - self.p0).cross(self.p2 - self.p0)
        # self.n /= self.n.norm()

        if self.n.norm() == 0:
            raise ValueError("Degenerate triangle")
        
        self.d = -self.n.dot(self.p0)

        self.ref_z = max(self.p0.z, self.p1.z, self.p2.z)
        self.min_z = min(self.p0.z, self.p1.z, self.p2.z)
    
    def within_2d_proj(self, x: float, y: float, eps: float = 1e-6) -> bool:
        """
            Check if (x, y) lies within the triangle's projection onto XY.

            Uses barycentric coordinates. Works regardless of triangle orientation in 3D,
            as long as its projection is non-degenerate.
        """
        A, B, C = self.p0, self.p1, self.p2
        v0 = Coord.math(C.x - A.x, C.y - A.y, 0)   
        v1 = Coord.math(B.x - A.x, B.y - A.y, 0)  
        v2 = Coord.math(x - A.x, y - A.y, 0)

        dot00 = v0.dot_2D(v0)
        dot01 = v0.dot_2D(v1)
        dot02 = v0.dot_2D(v2)
        dot11 = v1.dot_2D(v1) 
        dot12 = v1.dot_2D(v2)

        denom = dot00 * dot11 - dot01 * dot01
        if abs(denom) < eps: return False
        inv = 1.0 / denom

        u = (dot11 * dot02 - dot01 * dot12) * inv
        v = (dot00 * dot12 - dot01 * dot02) * inv

        return (u >= -eps) and (v >= -eps) and (u + v <= 1.0 + eps)

    def z_at(self,x: float, y: float) -> float:
        """ Compute z on the plane at XY = (x, y). """
        if abs(self.n.z) < 1e-8:
            raise ValueError("Normal z must be greater than 0")
        return (-(self.d + self.n.x*x + self.n.y*y) / self.n.z)

    def project_to_world(self, x: float, y: float) -> Coord:
        """ Lift a 2D XY point to a 3D world point that lies on this triangle's plane. """
        z = self.z_at(x, y)
        return Coord.math(x, y, z)



class Receiver:
    """
        A polygon that can receive shadows.

        A receiver has:
        - one or more triangular faces (for computing height z at a given XY)
        - a 2D polygon boundary in world XY (must be CCW for clipping)
        - a shade level used later by rendering
    """
    def __init__(self, faces: List[Triangle], polygon: List[Coord], shade_level: ShadeLevel, id: int | None = None):
        self.faces = faces
        self.polygon = self._ensure_ccw(polygon)  

        self.shade_level = shade_level
        self.ref_z = max([f.ref_z for f in self.faces])
        self.min_z = min([f.min_z for f in self.faces])
        self.id = id

    def z_at(self, x: float, y: float) -> float:
        """ Find the z-height of this receiver at (x, y) by testing which face contains it. """
        for face in self.faces:
            if face.within_2d_proj(x, y): return face.z_at(x, y)
        return 0

    def project_to_world(self, x: float, y: float) -> Coord:
        """Lift (x, y) onto this receiver surface."""
        z = self.z_at(x, y)
        return Coord.math(x, y, z)

    @staticmethod
    def _ensure_ccw(poly: List[Coord]) -> List[Coord]:
        """ Ensure polygon winding is CCW (required for Sutherland–Hodgman clipping). """
        area = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i].x, poly[i].y
            x2, y2 = poly[(i+1) % len(poly)].x, poly[(i+1) % len(poly)].y
            area += x1*y2 - x2*y1
        return poly if area > 0 else list(reversed(poly))


# -----------------------------------------------------------------------------
# Shadow builder
# -----------------------------------------------------------------------------
class Shadows:
    """
        Builds a lightweight 3D world representation and casts "noon" shadows.

        High-level approach:
        1) Approximate the caster's shadow footprint as an ellipse polygon in XY.
        2) For each receiver (sorted high -> low):
        - intersect ellipse polygon with receiver polygon = base shadow region
        - subtract holes created by higher receivers that overlap this region
        - project resulting polygons to screen space using receiver height function
        - rasterize into a small per-shadow surface and return as RenderObj
    """

    def __init__(self, ellipse_samples: int = 16):
        self.receivers = []
        self.ellipse_samples = ellipse_samples

    def add_receiver(self, receiver: Receiver) -> None:
        """ Register a surface that can receive shadows. """
        self.receivers.append(receiver)

    def reset_receivers(self) -> None:
        self.receivers = []

    def update(self) -> None:
        """ Maintain high-to-low ordering for occlusion logic. """
        self.receivers.sort(key=lambda r: r.ref_z, reverse=True)

    def get_shadow_objs(self, ellipse: EllipseData) -> List[RenderObj]:
        """
            Build RenderObj shadow sprites for the given ellipse caster.
            Returns a list of RenderObj, one per receiver that receives shadow.
        """

        render_obs: List[RenderObj] = []

        higher = []
        self.receivers.sort(key=lambda r: r.ref_z, reverse=True)
        ellipse_poly = self.generate_ellipse_poly(ellipse, samples=self.ellipse_samples)
        ellipse_bbox  = self._bbox_xy(ellipse_poly)

        for receiver in self.receivers:

            # Quick checks to discount recievers 
            if receiver.min_z >= ellipse.center.z: continue
            if not self._bbox_overlaps(ellipse_bbox, self._bbox_xy(receiver.polygon), pad=1e-6): continue

            # Base region on this receiver
            region_in_shadow = self.poly_intersection(ellipse_poly, receiver.polygon)
            if len(region_in_shadow) < 3: continue

            # Decide which higher receivers actually steal rays here and collect 'holes'
            hole_polys_xy = []
            for higher_receiver in higher:
                overlap = self.poly_intersection(region_in_shadow, higher_receiver.polygon)
                if self.poly_centroid(overlap):
                    reciever_hieght = receiver.min_z
                    higher_reciver_hieght = higher_receiver.min_z

                    # double check the higher z > reciever z and add it holes
                    if (higher_reciver_hieght < ellipse.center.z) and (higher_reciver_hieght > reciever_hieght + 1e-4):
                        hole_polys_xy.append(overlap)

            # reciever truly receives shadow so it can occlude things below
            higher.append(receiver)

            # Project base + holes to screen using this receiver’s plane
            min_x = min_y = float("inf")
            max_x = max_y = float("-inf")
            base_screen, holes_screen = [], []

            # Construct shadow poly in view coords that hits reciever
            for point in region_in_shadow:
                point_3d = receiver.project_to_world(point.x, point.y)
                point_3d.z = min(point_3d.z, max(ellipse.center.z - SHADOW_CLAMP, 1)) # Keeps shadows from being above player
                px, py = point_3d.as_view_coord()
                base_screen.append((px, py))
                min_x, max_x, min_y, max_y = min(min_x, px), max(max_x, px), min(min_y, py), max(max_y, py)

            # Construct polys to remove from reciever shadow poly in view coords
            for hole_xy in hole_polys_xy:
                holes = []
                for point in hole_xy:
                    point_3d = receiver.project_to_world(point.x, point.y)
                    point_3d.z = min(point_3d.z, ellipse.center.z)
                    px, py = point_3d.as_view_coord()
                    holes.append((px, py))
                    min_x, max_x, min_y, max_y = min(min_x, px), max(max_x, px), min(min_y, py), max(max_y, py)
                holes_screen.append(holes)


            if not base_screen: continue

            # Alpha & softness from height
            centriod = self.poly_centroid(region_in_shadow)
            reciever_centriod_height = receiver.z_at(centriod.x, centriod.y)
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

            # Punch holes by drawing them into a mask and subtracting
            if holes_screen:
                occ = pygame.Surface((s_w, s_h), pygame.SRCALPHA)
                for hole in holes_screen:
                    pygame.draw.polygon(occ, (0, 0, 0, 255), self._get_local_poly(offset_x, offset_y, hole))
                
                occ = self._blur_surface(occ, passes=1)
                shadow_surf.blit(occ, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

            # Place the shadow sprite at the center of its bounding box
            x, y = min_x + (max_x - min_x) / 2, min_y + (max_y - min_y) / 2
            render_obs.append(
                RenderObj(
                    None,
                    np.array([x, y]),
                    (receiver.shade_level, centriod.x, centriod.y, receiver.ref_z),
                    isShadow=True,
                    img=shadow_surf,
                )
            )

        return render_obs
    

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    

    @staticmethod
    def _get_local_poly(offset_x: int, offset_y: int, poly: List[Coord]) -> List[Coord]:
        """Convert screen-space points into local surface pixel coordinates."""
        return [(int(round(x - offset_x)), int(round(y - offset_y))) for (x, y) in poly]

    @staticmethod
    def get_alpha(height: float) -> int:
        """Map a height gap to alpha (0..255)."""
        t = max(0.0, min(1.0, height / 8.0))
        return int(120 * (1.0 - t) + 50 * t)
    
    # -------------------------------------------------------------------------
    #  Polygon clipping (Sutherland–Hodgman)
    # -------------------------------------------------------------------------

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

            if not inp: break

            prev = inp[-1]
            prev_in = Shadows.side(prev, a, b) >= -1e-6

            for cur in inp:
                cur_in = Shadows.side(cur, a, b) >= -1e-6

                if cur_in:
                    if not prev_in:
                        out.append(Shadows.intersect(prev, cur, a, b))
                    out.append(cur)
                else:
                    if prev_in:
                        out.append(Shadows.intersect(prev, cur, a, b))

                prev, prev_in = cur, cur_in

        return out

    # -------------------------------------------------------------------------
    # Ellipse sampling
    # -------------------------------------------------------------------------

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
        
        return pts
    
    # -------------------------------------------------------------------------
    # Misc geometry
    # -------------------------------------------------------------------------

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
    def _bbox_xy(poly: List[Coord]) -> Tuple[float,float,float,float]:
        """(min_x, min_y, max_x, max_y) in world XY."""
        xs = [p.x for p in poly]; ys = [p.y for p in poly]
        return (min(xs), min(ys), max(xs), max(ys))

    @staticmethod
    def _bbox_overlaps(
        a: Tuple[float,float,float,float],
        b: Tuple[float,float,float,float],
        pad: float = 0.0
    ) -> bool:
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
