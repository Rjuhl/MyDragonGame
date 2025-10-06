import math
import pygame
import numpy as np
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

    def __init__(self, ellipse_samples: int = 48):
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
        """ Gets shadows to render cast by an ellipse """
        render_obs = []        
        ellipse_poly = self.generate_ellipse_poly(ellipse, samples=self.ellipse_samples)

        higher = []
        for reciever in self.receivers: # Note this should be sorted already
            
            # If receiver is above caster it cannot recieve a shadow
            if reciever.min_z > ellipse.center.z: continue

            region_in_shadow = self.poly_intersection(ellipse_poly, reciever.polygon)

            # If there is no region overlap continue
            if len(region_in_shadow) < 3: continue

            for higher_reciever in higher: # Could cache intersections for speed up if needed
                overlap = self.poly_intersection(region_in_shadow, higher_reciever.polygon)
                if (centroid := self.poly_centroid(overlap)):
                    reciever_z = reciever.z_at(centroid.x, centroid.y)
                    higher_reciever_z = higher_reciever.z_at(centroid.x, centroid.y)

                    # double check the higher z > reciever z and cut out difference
                    if (higher_reciever_z < ellipse.center.z) and (higher_reciever_z > reciever_z + 1e-4):
                        region_in_shadow = self.poly_difference(region_in_shadow, higher_reciever.polygon)
                        if len(region_in_shadow) < 3: break

            # Only continue if region_in_shadow forms a poly
            if (centroid := self.poly_centroid(region_in_shadow)):
                higher.append(reciever)

                # Get alpha 
                reciever_centriod_height = reciever.z_at(centroid.x, centroid.y)
                hgap = max(0.0, ellipse.center.z - reciever_centriod_height)
                alpha = self.get_alpha(hgap)

                # Get the shadow poly as point in screen coords
                screen_points = []
                min_x = min_y = float('inf')
                max_x = max_y = -float('inf')
                for point in region_in_shadow:
                    point_3d = reciever.project_xy_to_world(point.x, point.y)
                    px, py = point_3d.as_view_coord()
                    screen_points.append([px, py])
                    min_x, max_x, min_y, max_y = min(min_x, px), max(max_x, px), min(min_y, py), max(max_y, py)
                
                # Create shadow img to later render
                pad = 1
                s_w = max(1, int(math.ceil(max_x - min_x))) + 2 * pad
                s_h = max(1, int(math.ceil(max_y - min_y))) + 2 * pad
                offset_x, offset_y = int(math.floor(min_x)) - pad, int(math.floor(min_y)) - pad
                polygon_local = [(int(round(x - offset_x)), int(round(y - offset_y))) for x, y in screen_points]
                shadow_img = self.draw_shadow_poly(polygon_local, (s_w, s_h), alpha) 
                            
                render_obs.append(RenderObj(
                    None, np.array([min_x, min_y]),
                    (reciever.shade_level, centroid.x, centroid.y, reciever.ref_z),
                    isShadow=True, img=shadow_img
                ))

        return render_obs

    @staticmethod
    def draw_shadow_poly(polygon: List[Tuple[int, int]], surface_size: Tuple[int, int], alpha: int) -> pygame.Surface:
        """ Draws a polygon onto pygame surface (point must be locally offset)"""
        surf = pygame.Surface(surface_size, pygame.SRCALPHA)
        pygame.draw.polygon(surf, (0, 0, 0, alpha), polygon)
        return surf


    @staticmethod
    def get_alpha(height: float) -> int:
        t = max(0.0, min(1.0, height / 8.0))
        return int(180 * (1.0 - t) + 50 * t)

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
    def clip(subject: List[Coord], clipper: List[Coord], intersection: bool = True) -> List[Coord]:
        """
        Sutherland–Hodgman clipping with a convex CCW clipper.
        If intersection=True: keep the LEFT side of each CCW clip edge (subject ∩ clipper).
        If intersection=False: keep the RIGHT side (subject \ clipper) — single-ring result.
        """
        # Flip the half-plane we consider "inside" for difference:
        sign = 1.0 if intersection else -1.0

        out = subject[:]
        for i in range(len(clipper)):
            a, b = clipper[i], clipper[(i + 1) % len(clipper)]
            inp, out = out, []

            if not inp:
                break

            prev = inp[-1]
            prev_in = (Shadows.side(prev, a, b) * sign) >= -1e-8

            for cur in inp:
                cur_in = (Shadows.side(cur, a, b) * sign) >= -1e-8

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
    def poly_intersection(subject: List[Coord], clipper: List[Coord]) -> List[Coord]:
        """CCW polygon of subject ∩ clipper (clipper must be convex & CCW)."""
        return Shadows.clip(subject, clipper, intersection=True)

    @staticmethod
    def poly_difference(subject: List[Coord], hole: List[Coord]) -> List[Coord]:
        """
        CCW polygon approximating subject hole by keeping the exterior of the CCW 'hole'.
        Note: returns a single ring; if the true result is multi-part, this wont represent holes.
        """
        return Shadows.clip(subject, hole, intersection=False)

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

    @staticmethod
    def poly_centroid(poly: List[Coord]) -> Optional[Coord]:
        """ Computes rough 2D centriod """
        if len(poly) < 3: return None
        sx = sy = 0
        for p in poly:
            sx += p.x
            sy += p.y

        return Coord.math(sx / len(poly), sy / len(poly), 0)