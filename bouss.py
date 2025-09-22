"""
Boussinesq vertical stress beneath a uniformly loaded rectangular (strip) area.

We compute the stress via Gaussian quadrature integration of the Boussinesq point-load kernel:
  sigma_z = q ∬ K(x - s, y - t, z) ds dt
  with K(dx, dy, z) = 3 z^3 / (2π (dx^2 + dy^2 + z^2)^(5/2))

The rectangle is centered at `center_xy` and rotated by `rotation_deg` about +z.
Depth z is positive downward, surface at z = 0.

This approach is robust and accurate for interactive usage (n_gauss ~ 12-20).
"""

from __future__ import annotations

import math
from typing import Iterable, Tuple

import numpy as np


PI = math.pi
TWOPI = 2.0 * PI


def _deg_to_rad(angle_deg: float) -> float:
	return angle_deg * PI / 180.0


def _rotate_points_xy(points_xy: np.ndarray, rotation_deg: float) -> np.ndarray:
	"""Rotate 2D points in the xy-plane by rotation_deg about origin.

	points_xy: array of shape (..., 2)
	returns rotated array of same shape
	"""
	if rotation_deg == 0.0:
		return points_xy
	theta = _deg_to_rad(rotation_deg)
	c = math.cos(theta)
	s = math.sin(theta)
	rot = np.array([[c, -s], [s, c]], dtype=float)
	return points_xy @ rot.T



def sigma_z_infinite_strip(
	points_xyz: np.ndarray,
	width_b: float,
	uniform_pressure_q: float,
	poisson_ratio: float = 0.3,
	rotation_deg: float = 0.0,
	center_xy: Tuple[float, float] = (0.0, 0.0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
	"""Analytical stresses for an infinitely long uniformly loaded strip (length → ∞).

	The strip is centered at `center_xy`, aligned with its length along the local y-axis,
	with width `width_b` along local x in [-B/2, B/2]. Rotation rotates the strip about z.

	Returns: (sigma_z, sigma_x, sigma_y, tau_xz) arrays of shape (N,)

	Formula (plane strain, book's strip result):
	  σz = (q/π)[ arctan((x + b)/z) + arctan((b − x)/z) ]  for z > 0
	  σx = ν σz - (q/π)[sinα cos(2β) - α]
	  σy = ν σz
	  τxz = (q/π) sinα sin(2β)

	Surface limits (z = 0):
	  σz = q         for |x| < b
	  σz = q/2       for |x| = b   ← edge half-value (correction)
	  σz = 0         for |x| > b
	  σx = σy = τxz = 0 everywhere at surface
	"""
	if width_b <= 0:
		raise ValueError("width must be positive")
	pts = np.asarray(points_xyz, dtype=float)
	assert pts.ndim == 2 and pts.shape[1] == 3
	shifted_xy = pts[:, :2] - np.asarray(center_xy, dtype=float)
	local_xy = _rotate_points_xy(shifted_xy, -rotation_deg)
	x = local_xy[:, 0]
	z = pts[:, 2]
	if np.any(z < 0):
		raise ValueError("Depth z must be >= 0 (downwards)")

	b = 0.5 * width_b
	sig_z = np.empty_like(z, dtype=float)
	sig_x = np.empty_like(z, dtype=float)
	sig_y = np.empty_like(z, dtype=float)
	tau_xz = np.empty_like(z, dtype=float)

	# Analytical expression for z > 0
	# Clamp z to a small positive epsilon to capture z -> 0+ limits without overrides
	z_epsilon = max(1e-8 * width_b, 1e-9)
	zpos = np.where(z < z_epsilon, z_epsilon, z)
	beta_prime_t = np.arctan((x - b) / zpos)
	sss = np.arctan((x + b) / zpos)
	alpha_t = sss - beta_prime_t
	beta_t = alpha_t / 2 + beta_prime_t

	# Calculate all stress components
	term_z = np.sin(alpha_t) * np.cos(2 * beta_t) + alpha_t
	term_x = -np.sin(alpha_t) * np.cos(2 * beta_t) + alpha_t
	term_xz = np.sin(alpha_t) * np.sin(2 * beta_t)

	sig_zpos = (uniform_pressure_q / PI) * term_z
	sig_xpos = (uniform_pressure_q / PI) * term_x
	sig_ypos = poisson_ratio * sig_zpos
	tau_xz_pos = (uniform_pressure_q / PI) * term_xz

	# Assign for all points (including z ~ 0, via clamped z)
	sig_z[:] = sig_zpos
	sig_x[:] = sig_xpos
	sig_y[:] = sig_ypos
	tau_xz[:] = tau_xz_pos

	# Enforce traction boundary conditions exactly at the free surface (z -> 0+)
	surface_mask = pts[:, 2] <= z_epsilon
	if np.any(surface_mask):
		# Inside strip (|x| < b) -> sigma_z = q; at edge -> q/2; outside -> 0
		x_all = x
		edge_tol = max(1e-6 * width_b, 1e-8)
		inside_mask = surface_mask & (np.abs(x_all) < b - edge_tol)
		edge_mask = surface_mask & (np.abs(np.abs(x_all) - b) <= edge_tol)
		outside_mask = surface_mask & (np.abs(x_all) > b + edge_tol)
		sig_z[inside_mask] = uniform_pressure_q
		sig_z[edge_mask] = 0.5 * uniform_pressure_q
		sig_z[outside_mask] = 0.0
		# Shear and in-plane stresses vanish at the free surface
		sig_x[surface_mask] = 0.0
		sig_y[surface_mask] = 0.0
		tau_xz[surface_mask] = 0.0

	return sig_z, sig_x, sig_y, tau_xz


def integrate_circular_sigma_z(
    points_xyz: np.ndarray,
    radius_a: float,
    uniform_pressure_q: float,
    center_xy: Tuple[float, float] = (0.0, 0.0),
    n_r: int = 61,
    n_theta: int = 41,
) -> np.ndarray:
	"""Vertical stress under a uniformly loaded circular footing by explicit polar integration.

	We integrate Boussinesq's kernel in polar coordinates over the loaded disk of radius `radius_a`:
	  σz(x,y,z) = q ∫₀^{2π} ∫₀^{a} [ 3 z^3 / (2π R^5) ] ρ dρ dθ,
	with R^2 = (x - ρ cosθ)^2 + (y - ρ sinθ)^2 + z^2.

	- points_xyz: (N,3) array with z ≥ 0
	- radius_a: footing radius (> 0)
	- uniform_pressure_q: uniform pressure intensity
	- center_xy: circle center translation
	- n_r, n_theta: odd counts for Simpson integration (≥ 3)
	"""
	pts = np.asarray(points_xyz, dtype=float)
	assert pts.ndim == 2 and pts.shape[1] == 3
	if radius_a <= 0:
		raise ValueError("radius must be positive")
	if np.any(pts[:, 2] < 0):
		raise ValueError("Depth z must be >= 0 (downwards)")
	if n_r < 3 or n_theta < 3:
		raise ValueError("n_r and n_theta must be >= 3")
	# Ensure odd for Simpson's rule
	if n_r % 2 == 0:
		n_r += 1
	if n_theta % 2 == 0:
		n_theta += 1

	# Adapt integration resolution for large evaluation sets to keep UI responsive
	num_points = pts.shape[0]
	if num_points >= 10000:
		n_r = max(3, min(n_r, 31)) | 1
		n_theta = max(3, min(n_theta, 25)) | 1
	elif num_points >= 4000:
		n_r = max(3, min(n_r, 41)) | 1
		n_theta = max(3, min(n_theta, 31)) | 1
	elif num_points >= 1000:
		n_r = max(3, min(n_r, 51)) | 1
		n_theta = max(3, min(n_theta, 41)) | 1

	# Local coordinates (circle is rotationally symmetric; rotation not needed)
	shifted_xy = pts[:, :2] - np.asarray(center_xy, dtype=float)
	x_all = shifted_xy[:, 0]
	y_all = shifted_xy[:, 1]
	z_all = pts[:, 2]
	# Clamp z for near-surface limit (avoid singularity at z = 0)
	# Chosen slightly larger epsilon for stability in dense heatmaps
	z_eps = max(1e-6 * radius_a, 1e-6)
	zpos_all = np.where(z_all < z_eps, z_eps, z_all)

	# Simpson nodes and weights in r and theta
	r_nodes = np.linspace(0.0, radius_a, n_r)
	theta_nodes = np.linspace(0.0, TWOPI, n_theta)
	wr = np.ones(n_r)
	wr[1:-1:2] = 4.0
	wr[2:-2:2] = 2.0
	wt = np.ones(n_theta)
	wt[1:-1:2] = 4.0
	wt[2:-2:2] = 2.0
	dr = radius_a / (n_r - 1)
	dtheta = TWOPI / (n_theta - 1)
	# Combine Simpson factors (Δ/3) and polar jacobian ρ
	area_weights_2d = ((wr * dr) / 3.0)[:, None] * ((wt * dtheta) / 3.0)[None, :]  # (nr,nth)
	area_weights_2d = area_weights_2d * r_nodes[:, None]

	# Build grids for evaluation
	r_grid = r_nodes[None, :, None]  # (1,nr,1)
	theta_grid = theta_nodes[None, None, :]  # (1,1,nth)
	cos_t = np.cos(theta_grid)
	sin_t = np.sin(theta_grid)

	# Batched evaluation to cap memory usage
	num_points = pts.shape[0]
	sigma_z = np.empty(num_points, dtype=float)

	# Estimate a safe batch size to keep memory reasonable (~64MB transient)
	arrays_per_batch = 5  # dx, dy, R2, R5, K
	elems_per_point = n_r * n_theta
	bytes_per_point = arrays_per_batch * elems_per_point * 8
	target_bytes = 64 * 1024 * 1024
	batch_size = max(1, int(target_bytes // max(bytes_per_point, 1)))
	batch_size = min(batch_size, num_points)
	if batch_size <= 0:
		batch_size = 1

	for start in range(0, num_points, batch_size):
		stop = min(start + batch_size, num_points)
		xb = x_all[start:stop][:, None, None]
		yb = y_all[start:stop][:, None, None]
		zb = zpos_all[start:stop][:, None, None]

		dx = xb - r_grid * cos_t  # (B,nr,nth)
		dy = yb - r_grid * sin_t  # (B,nr,nth)
		R2 = dx * dx + dy * dy + zb * zb
		R5 = R2 ** 2.5
		K = (3.0 * (zb ** 3)) / (TWOPI * R5)
		# Weighted sum over disk for the batch
		# Result shape: (B,)
		sigma_z[start:stop] = uniform_pressure_q * np.tensordot(
			K, area_weights_2d, axes=([1, 2], [0, 1])
		)

	# Near-surface analytical limit at z -> 0+
	r_all = np.hypot(x_all, y_all)
	surface_mask = z_all <= z_eps
	edge_tol = max(1e-4 * radius_a, 1e-5)
	inside_mask = surface_mask & (r_all < radius_a - edge_tol)
	edge_mask = surface_mask & (np.abs(r_all - radius_a) <= edge_tol)
	outside_mask = surface_mask & (r_all > radius_a + edge_tol)
	sigma_z[inside_mask] = uniform_pressure_q
	sigma_z[edge_mask] = 0.5 * uniform_pressure_q
	sigma_z[outside_mask] = 0.0

	return sigma_z


def generate_line_points(
	start_xyz: Iterable[float],
	end_xyz: Iterable[float],
	num_points: int,
) -> np.ndarray:
	"""Generate points along an arbitrary 3D line, inclusive of endpoints."""
	p0 = np.asarray(start_xyz, dtype=float)
	p1 = np.asarray(end_xyz, dtype=float)
	if num_points < 2:
		raise ValueError("num_points must be >= 2")
	ts = np.linspace(0.0, 1.0, num_points)
	pts = (1.0 - ts)[:, None] * p0[None, :] + ts[:, None] * p1[None, :]
	return pts


def generate_plane_grid(
	plane: str,
	const_value: float,
	x_bounds: Tuple[float, float],
	y_bounds: Tuple[float, float],
	nx: int,
	ny: int,
	z_bounds: Tuple[float, float] | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
	"""Generate a grid of (x, y, z) points over a specified plane.

	plane: one of {"xy", "xz", "yz"}
	- For "xy": const_value is z, and x_bounds, y_bounds are used.
	- For "xz": const_value is y, use x_bounds and z_bounds.
	- For "yz": const_value is x, use y_bounds and z_bounds.

	Returns: (X, Y, Z) each shaped (ny, nx), using numpy.meshgrid with indexing="xy".
	"""
	if nx < 2 or ny < 2:
		raise ValueError("nx and ny must be >= 2")
	plane = plane.lower()
	if plane not in {"xy", "xz", "yz"}:
		raise ValueError("plane must be 'xy', 'xz', or 'yz'")

	if plane == "xy":
		x = np.linspace(x_bounds[0], x_bounds[1], nx)
		y = np.linspace(y_bounds[0], y_bounds[1], ny)
		X, Y = np.meshgrid(x, y, indexing="xy")
		Z = np.full_like(X, const_value, dtype=float)
	elif plane == "xz":
		x = np.linspace(x_bounds[0], x_bounds[1], nx)
		z = np.linspace(z_bounds[0], z_bounds[1], ny)
		X, Z = np.meshgrid(x, z, indexing="xy")
		Y = np.full_like(X, const_value, dtype=float)
	else:  # "yz"
		y = np.linspace(y_bounds[0], y_bounds[1], nx)
		z = np.linspace(z_bounds[0], z_bounds[1], ny)
		Y, Z = np.meshgrid(y, z, indexing="xy")
		X = np.full_like(Y, const_value, dtype=float)

	return X, Y, Z


def integrate_circular_stress_full(
	points_xyz: np.ndarray,
	radius_a: float,
	uniform_pressure_q: float,
	center_xy: Tuple[float, float] = (0.0, 0.0),
	n_r: int = 61,
	n_theta: int = 41,
) -> Tuple[np.ndarray, np.ndarray]:
	"""Vertical and shear stresses (sigma_z, tau_rz) under a circular footing.

	Integrates the Boussinesq point-load stress tensor over the loaded disk with uniform pressure q.
	Uses Simpson integration in polar coordinates with batching to control memory.
	Returns only sigma_z and tau_rz (sigma_r and sigma_theta removed).
	"""
	pts = np.asarray(points_xyz, dtype=float)
	assert pts.ndim == 2 and pts.shape[1] == 3
	if radius_a <= 0:
		raise ValueError("radius must be positive")
	if np.any(pts[:, 2] < 0):
		raise ValueError("Depth z must be >= 0 (downwards)")
	if n_r < 3 or n_theta < 3:
		raise ValueError("n_r and n_theta must be >= 3")
	if n_r % 2 == 0:
		n_r += 1
	if n_theta % 2 == 0:
		n_theta += 1

	# Adapt nodes for large grids
	num_points = pts.shape[0]
	if num_points >= 10000:
		n_r = max(3, min(n_r, 31)) | 1
		n_theta = max(3, min(n_theta, 25)) | 1
	elif num_points >= 4000:
		n_r = max(3, min(n_r, 41)) | 1
		n_theta = max(3, min(n_theta, 31)) | 1
	elif num_points >= 1000:
		n_r = max(3, min(n_r, 51)) | 1
		n_theta = max(3, min(n_theta, 41)) | 1

	# Local coords and clamps
	shifted_xy = pts[:, :2] - np.asarray(center_xy, dtype=float)
	x_all = shifted_xy[:, 0]
	y_all = shifted_xy[:, 1]
	z_all = pts[:, 2]
	z_eps = max(1e-6 * radius_a, 1e-6)
	zpos_all = np.where(z_all < z_eps, z_eps, z_all)

	# Simpson nodes/weights and grids
	r_nodes = np.linspace(0.0, radius_a, n_r)
	theta_nodes = np.linspace(0.0, TWOPI, n_theta)
	wr = np.ones(n_r)
	wr[1:-1:2] = 4.0
	wr[2:-2:2] = 2.0
	wt = np.ones(n_theta)
	wt[1:-1:2] = 4.0
	wt[2:-2:2] = 2.0
	dr = radius_a / (n_r - 1)
	dtheta = TWOPI / (n_theta - 1)
	area_weights_2d = ((wr * dr) / 3.0)[:, None] * ((wt * dtheta) / 3.0)[None, :]
	area_weights_2d = area_weights_2d * r_nodes[:, None]

	r_grid = r_nodes[None, :, None]
	theta_grid = theta_nodes[None, None, :]
	cos_t = np.cos(theta_grid)
	sin_t = np.sin(theta_grid)

	# Outputs - only sigma_z and tau_rz components
	sig_xz = np.empty(num_points, dtype=float)
	sig_yz = np.empty(num_points, dtype=float)
	sig_zz = np.empty(num_points, dtype=float)

	# Batch size estimate
	arrays_per_batch = 5  # dx, dy, R2, R5, K_zz, K_xz, K_yz
	elems_per_point = n_r * n_theta
	bytes_per_point = arrays_per_batch * elems_per_point * 8
	target_bytes = 64 * 1024 * 1024
	batch_size = max(1, int(target_bytes // max(bytes_per_point, 1)))
	batch_size = min(batch_size, num_points)
	if batch_size <= 0:
		batch_size = 1

	C3 = 3.0 / (2.0 * PI)

	for start in range(0, num_points, batch_size):
		stop = min(start + batch_size, num_points)
		xb = x_all[start:stop][:, None, None]
		yb = y_all[start:stop][:, None, None]
		zb = zpos_all[start:stop][:, None, None]

		dx = xb - r_grid * cos_t
		dy = yb - r_grid * sin_t
		R2 = dx * dx + dy * dy + zb * zb
		R5 = R2 ** 2.5

		K_zz = C3 * (zb ** 3) / R5
		K_xz = C3 * dx * (zb ** 2) / R5
		K_yz = C3 * dy * (zb ** 2) / R5

		Aw = area_weights_2d
		sig_zz[start:stop] = uniform_pressure_q * np.tensordot(K_zz, Aw, axes=([1, 2], [0, 1]))
		sig_xz[start:stop] = uniform_pressure_q * np.tensordot(K_xz, Aw, axes=([1, 2], [0, 1]))
		sig_yz[start:stop] = uniform_pressure_q * np.tensordot(K_yz, Aw, axes=([1, 2], [0, 1]))

	# Convert to cylindrical shear stress tau_rz
	phi = np.arctan2(y_all, x_all)
	c = np.cos(phi)
	s = np.sin(phi)
	tau_rz = sig_xz * c + sig_yz * s

	# Near-surface limit: enforce traction boundary conditions at z=0
	surface_mask = z_all <= z_eps
	if np.any(surface_mask):
		# tau_rz must be zero at the free surface
		tau_rz[surface_mask] = 0.0
		# Enforce sigma_z limits to match applied traction
		r_all = np.hypot(x_all, y_all)
		edge_tol = max(1e-4 * radius_a, 1e-5)
		inside_mask = surface_mask & (r_all < radius_a - edge_tol)
		edge_mask = surface_mask & (np.abs(r_all - radius_a) <= edge_tol)
		outside_mask = surface_mask & (r_all > radius_a + edge_tol)
		sigma_z = sig_zz.copy()
		sigma_z[inside_mask] = uniform_pressure_q
		sigma_z[edge_mask] = 0.5 * uniform_pressure_q
		sigma_z[outside_mask] = 0.0
	else:
		sigma_z = sig_zz

	return sigma_z, tau_rz