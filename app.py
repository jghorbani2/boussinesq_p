import math
from typing import Tuple
import io

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html, callback_context as ctx
from dash.exceptions import PreventUpdate

from bouss import (
	generate_line_points,
	generate_plane_grid,
	sigma_z_infinite_strip,
	integrate_circular_sigma_z,
	integrate_circular_stress_full,
)


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "Boussinesq Strip Stress Analysis"

# Configure app for better JavaScript loading
app.config.suppress_callback_exceptions = True


def svg_strip_diagram() -> html.Div:
	# Replace with static asset SVG
	return html.Div(html.Img(src="/assets/strip.svg", style={"width": "100%", "maxWidth": "520px", "height": "auto", "display": "block", "margin": "6px 0"}))


def svg_circle_diagram() -> html.Div:
	# Replace with static asset SVG
	return html.Div(html.Img(src="/assets/circle.svg", style={"width": "100%", "maxWidth": "520px", "height": "auto", "display": "block", "margin": "6px 0"}))


def svg_trap_diagram() -> html.Div:
	# Replace with static asset SVG
	return html.Div(html.Img(src="/assets/trapezoid.svg", style={"width": "100%", "maxWidth": "520px", "height": "auto", "display": "block", "margin": "6px 0"}))

def layout_controls_strip() -> html.Div:
	return html.Div(
		[
			html.Div(
				[
					html.H3("Footing and Load"),
					html.Div(
						[
							html.Label("Uniform pressure q (kPa)"),
							dcc.Input(id="q", type="number", value=100.0, step=1.0),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Label("Poisson's ratio ν"),
							dcc.Input(id="poisson_ratio", type="number", value=0.3, step=0.01, min=0.0, max=0.5),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Label("Width B (m)"),
							dcc.Input(id="width_b", type="number", value=2.0, step=0.1),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("Center x₀ (m)"),
									dcc.Input(id="x0", type="number", value=0.0, step=0.1),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Center y₀ (m)"),
									dcc.Input(id="y0", type="number", value=0.0, step=0.1),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Rotation (°)"),
									dcc.Input(id="angle", type="number", value=0.0, step=1.0),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
				],
				className="section",
			),
			html.Div(
				[
					html.H3("Line Plot (arbitrary 3D path)"),
					html.Div(
						[
							html.Div(
								[
									html.Label("Start point x, y, z (m)"),
									dcc.Input(id="lx0", type="number", value=-5.0, step=0.1, placeholder="x"),
									dcc.Input(id="ly0", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="lz0", type="number", value=0.0, step=0.1, placeholder="z"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("End point x, y, z (m)"),
									dcc.Input(id="lx1", type="number", value=5.0, step=0.1, placeholder="x"),
									dcc.Input(id="ly1", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="lz1", type="number", value=10.0, step=0.1, placeholder="z"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					# Removed number of points (fixed resolution)
					html.Button("Compute Line Plot", id="btn_line"),
				],
				className="section",
			),
			html.Div(
				[
					html.H3("Heatmap (plane slice)"),
					html.Div(
						[
							html.Div(
								[
									html.Label("Plane type"),
									dcc.Dropdown(
										id="plane",
										options=[
											{"label": "XY plane at constant z", "value": "xy"},
											{"label": "XZ plane at constant y", "value": "xz"},
											{"label": "YZ plane at constant x", "value": "yz"},
										],
										value="xy",
									),
							],
							className="input-group",
						),
						html.Div(
							[
								html.Label("Constant value (m)"),
								dcc.Input(id="const_val", type="number", value=2.0, step=0.1),
							],
							className="input-group",
						),
					],
					className="input-row",
				),
					html.Div(
						[
							html.Div(
								[
									html.Label("X range (m)"),
									dcc.Input(id="xmin", type="number", value=-6.0, step=0.5, placeholder="min"),
									dcc.Input(id="xmax", type="number", value=6.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Y range (m)"),
									dcc.Input(id="ymin", type="number", value=-6.0, step=0.5, placeholder="min"),
									dcc.Input(id="ymax", type="number", value=6.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("Z range (m, for XZ/YZ planes)"),
									dcc.Input(id="zmin", type="number", value=0.0, step=0.5, placeholder="min"),
									dcc.Input(id="zmax", type="number", value=10.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Grid resolution"),
									dcc.Input(id="nx", type="number", value=120, step=2, placeholder="nx"),
									dcc.Input(id="ny", type="number", value=120, step=2, placeholder="ny"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Label("Heatmap component"),
							dcc.Dropdown(
								id="heat_component",
								options=[
									{"label": "σz", "value": "sigma_z"},
									{"label": "σx", "value": "sigma_x"},
									{"label": "σy", "value": "sigma_y"},
									{"label": "τxz", "value": "tau_xz"},
								],
								value="sigma_z",
							),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Label("Display"),
							dcc.RadioItems(
								id="heat_display",
								options=[
									{"label": "Heatmap", "value": "heatmap"},
									{"label": "Isobar (contour)", "value": "isobar"},
								],
								value="heatmap",
							),
						],
						className="input-group",
					),
						html.Div(
							[
								html.Label("Isobar count"),
								dcc.Input(id="n_isobars", type="number", value=15, step=1, min=1, max=200),
							],
							className="input-group",
						),
					html.Button("Compute Heatmap", id="btn_heat"),
				],
				className="section",
			),
		],
		className="controls",
	)


def layout_controls_circle() -> html.Div:
	return html.Div(
		[
			html.Div(
				[
					html.H3("Footing and Load (Circular)"),
					html.Div(
						[
							html.Label("Uniform pressure q (kPa)"),
							dcc.Input(id="q_c", type="number", value=100.0, step=1.0),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Label("Radius a (m)"),
							dcc.Input(id="radius_a", type="number", value=2.0, step=0.1),
						],
						className="input-group",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("Center x₀ (m)"),
									dcc.Input(id="x0_c", type="number", value=0.0, step=0.1),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Center y₀ (m)"),
									dcc.Input(id="y0_c", type="number", value=0.0, step=0.1),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
				],
				className="section",
			),
			html.Div(
				[
					html.H3("Line Plot (arbitrary 3D path)"),
					html.Div(
						[
							html.Div(
								[
									html.Label("Start point x, y, z (m)"),
									dcc.Input(id="lx0_c", type="number", value=-5.0, step=0.1, placeholder="x"),
									dcc.Input(id="ly0_c", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="lz0_c", type="number", value=0.0, step=0.1, placeholder="z"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("End point x, y, z (m)"),
									dcc.Input(id="lx1_c", type="number", value=5.0, step=0.1, placeholder="x"),
									dcc.Input(id="ly1_c", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="lz1_c", type="number", value=10.0, step=0.1, placeholder="z"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Button("Compute Line Plot (Circle)", id="btn_line_c"),
				],
				className="section",
			),
			html.Div(
				[
					html.H3("Heatmap (plane slice)"),
					html.Div(
						[
							html.Div(
								[
									html.Label("Plane type"),
									dcc.Dropdown(
										id="plane_c",
										options=[
											{"label": "XY plane at constant z", "value": "xy"},
											{"label": "XZ plane at constant y", "value": "xz"},
											{"label": "YZ plane at constant x", "value": "yz"},
										],
										value="xy",
									),
							],
							className="input-group",
						),
						html.Div(
							[
								html.Label("Constant value (m)"),
								dcc.Input(id="const_val_c", type="number", value=2.0, step=0.1),
							],
							className="input-group",
						),
					],
					className="input-row",
				),
					html.Div(
						[
							html.Div(
								[
									html.Label("X range (m)"),
									dcc.Input(id="xmin_c", type="number", value=-6.0, step=0.5, placeholder="min"),
									dcc.Input(id="xmax_c", type="number", value=6.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
							html.Div(
								[
									html.Label("Y range (m)"),
									dcc.Input(id="ymin_c", type="number", value=-6.0, step=0.5, placeholder="min"),
									dcc.Input(id="ymax_c", type="number", value=6.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Div(
								[
									html.Label("Z range (m, for XZ/YZ planes)"),
									dcc.Input(id="zmin_c", type="number", value=0.0, step=0.5, placeholder="min"),
									dcc.Input(id="zmax_c", type="number", value=10.0, step=0.5, placeholder="max"),
								],
								className="input-group",
							),
                            html.Div(
                                [
                                    html.Label("Grid resolution"),
                                    dcc.Input(id="nx_c", type="number", value=80, step=2, placeholder="nx"),
                                    dcc.Input(id="ny_c", type="number", value=80, step=2, placeholder="ny"),
                                ],
                                className="input-group",
                            ),
						],
						className="input-row",
					),
					html.Div(
						[
							html.Label("Display"),
							dcc.RadioItems(
								id="heat_display_c",
								options=[
									{"label": "Heatmap", "value": "heatmap"},
									{"label": "Isobar (contour)", "value": "isobar"},
								],
								value="heatmap",
							),
						],
						className="input-group",
					),
						html.Div(
							[
								html.Label("Isobar count"),
								dcc.Input(id="n_isobars_c", type="number", value=15, step=1, min=1, max=200),
							],
							className="input-group",
						),
					html.Button("Compute Heatmap (Circle)", id="btn_heat_c"),
				],
				className="section",
			),
		],
		className="controls",
	)


def make_layout() -> html.Div:
	# Header
	header = html.Div(
		[
			html.Div(
				html.H2("Boussinesq Stress Analysis under Strip Footing"),
				className="header-content"
			),
			html.Div(
				html.Button("⚙️", id="settings-btn", className="settings-btn", title="Theme Settings"),
				className="header-actions"
			),
		],
		className="header",
	)

	# Strip tab content
	side_strip = html.Div(layout_controls_strip(), className="side")
	results_strip = html.Div(
		[
			dcc.Store(id="line_store"),
			dcc.Store(id="heat_store"),
			dcc.Download(id="download_line"),
			dcc.Download(id="download_heat"),
			html.Div(
				[
					html.H3("Line Plot Results", className="results-title"),
					svg_strip_diagram(),
					html.Div(
						[
							html.Label("Line component"),
							dcc.Dropdown(
								id="line_component",
								options=[
									{"label": "σz", "value": "sigma_z"},
									{"label": "σx", "value": "sigma_x"},
									{"label": "σy", "value": "sigma_y"},
									{"label": "τxz", "value": "tau_xz"},
								],
								value="sigma_z",
							),
						],
						className="input-group",
					),
					html.Div(dcc.Loading(dcc.Graph(id="line_fig", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Line CSV", id="btn_dl_line"),
					html.H3("Heatmap Results", className="results-title"),
					html.Div(dcc.Loading(dcc.Graph(id="heat_fig", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Heatmap CSV", id="btn_dl_heat"),
				],
				className="results-section",
			),
		],
		className="main-content",
	)
	strip_tab = dcc.Tab(label="Strip Footing", value="tab-strip", children=[
		html.Div([side_strip, results_strip], className="container")
	])

	# Circle tab content
	side_circle = html.Div(layout_controls_circle(), className="side")
	results_circle = html.Div(
		[
			dcc.Store(id="line_store_c"),
			dcc.Store(id="heat_store_c"),
			dcc.Download(id="download_line_c"),
			dcc.Download(id="download_heat_c"),
			html.Div(
				[
					html.H3("Line Plot Results (Circle)", className="results-title"),
					svg_circle_diagram(),
					html.Div(
						[
							html.Label("Line component"),
							dcc.Dropdown(
								id="line_component_c",
								options=[
									{"label": "σz", "value": "sigma_z"},
									{"label": "τrz", "value": "tau_rz"},
								],
								value="sigma_z",
							),
						],
						className="input-group",
					),
					html.Div(dcc.Loading(dcc.Graph(id="line_fig_c", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Line CSV (Circle)", id="btn_dl_line_c"),
					html.H3("Heatmap Results (Circle)", className="results-title"),
					html.Div(
						[
							html.Label("Heatmap component"),
							dcc.Dropdown(
								id="heat_component_c",
								options=[
									{"label": "σz", "value": "sigma_z"},
									{"label": "τrz", "value": "tau_rz"},
								],
								value="sigma_z",
							),
						],
						className="input-group",
					),
					html.Div(dcc.Loading(dcc.Graph(id="heat_fig_c", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Heatmap CSV (Circle)", id="btn_dl_heat_c"),
				],
				className="results-section",
			),
		],
		className="main-content",
	)
	circle_tab = dcc.Tab(label="Circular Footing", value="tab-circle", children=[
		html.Div([side_circle, results_circle], className="container")
	])

	# Trapezoidal Load tab content
	def layout_controls_trapezoid() -> html.Div:
		return html.Div(
			[
				html.Div(
					[
						html.H3("Trapezoidal Geometry and Load"),
						html.Div(
							[
								html.Div([
									html.Label("a₁ (m)"),
									dcc.Input(id="trap_a1", type="number", value=2.0, step=0.1),
								], className="input-group"),
								html.Div([
									html.Label("a₂ (m)"),
									dcc.Input(id="trap_a2", type="number", value=3.0, step=0.1),
								], className="input-group"),
								html.Div([
									html.Label("b (m)"),
									dcc.Input(id="trap_b", type="number", value=1.5, step=0.1, min=0.0),
								], className="input-group"),
								html.Div([
									html.Label("q (kPa)"),
									dcc.Input(id="trap_q", type="number", value=100.0, step=1.0, min=0.0),
								], className="input-group"),
							], className="input-row"),
					],
					className="section",
				),
				html.Div(
					[
						html.H3("Line Plot (arbitrary 3D path)"),
						html.Div(
							[
								html.Div([
									html.Label("Start point x, y, z (m)"),
									dcc.Input(id="trap_lx0", type="number", value=-5.0, step=0.1, placeholder="x"),
									dcc.Input(id="trap_ly0", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="trap_lz0", type="number", value=0.0, step=0.1, placeholder="z"),
								], className="input-group"),
							], className="input-row"),
						html.Div(
							[
								html.Div([
									html.Label("End point x, y, z (m)"),
									dcc.Input(id="trap_lx1", type="number", value=5.0, step=0.1, placeholder="x"),
									dcc.Input(id="trap_ly1", type="number", value=0.0, step=0.1, placeholder="y"),
									dcc.Input(id="trap_lz1", type="number", value=10.0, step=0.1, placeholder="z"),
								], className="input-group"),
							], className="input-row"),
						html.Button("Compute Line Plot (Trap)", id="btn_trap_line"),
					],
					className="section",
				),
				html.Div(
					[
						html.H3("Heatmap (XZ plane slice)"),
						html.Div(
							[
								html.Div([
									html.Label("X range (m)"),
									dcc.Input(id="trap_xmin", type="number", value=-6.0, step=0.5, placeholder="min"),
									dcc.Input(id="trap_xmax", type="number", value=6.0, step=0.5, placeholder="max"),
								], className="input-group"),
								html.Div([
									html.Label("Z range (m)"),
									dcc.Input(id="trap_zmin", type="number", value=0.0, step=0.5, placeholder="min"),
									dcc.Input(id="trap_zmax", type="number", value=10.0, step=0.5, placeholder="max"),
								], className="input-group"),
								html.Div([
									html.Label("Grid resolution"),
									dcc.Input(id="trap_nx", type="number", value=120, step=2, placeholder="nx"),
									dcc.Input(id="trap_nz", type="number", value=120, step=2, placeholder="nz"),
								], className="input-group"),
								html.Div([
									html.Label("Display"),
									dcc.RadioItems(id="trap_heat_display", options=[
										{"label": "Heatmap", "value": "heatmap"},
										{"label": "Isobar (contour)", "value": "isobar"},
									], value="heatmap"),
								], className="input-group"),
							html.Div([
								html.Label("Isobar count"),
								dcc.Input(id="trap_n_isobars", type="number", value=15, step=1, min=1, max=200),
							], className="input-group"),
						], className="input-row"),
						html.Button("Compute Heatmap (Trap)", id="btn_trap_heat"),
					],
					className="section",
				),
			],
			className="controls",
		)

	side_trap = html.Div(layout_controls_trapezoid(), className="side")
	results_trap = html.Div(
		[
			dcc.Store(id="trap_line_store"),
			dcc.Store(id="trap_heat_store"),
			dcc.Download(id="download_trap_line"),
			dcc.Download(id="download_trap_heat"),
			html.Div(
				[
					html.H3("Line Plot Results (Trapezoid)", className="results-title"),
					svg_trap_diagram(),
					html.Div(dcc.Loading(dcc.Graph(id="trap_line_fig", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Line CSV (Trap)", id="btn_dl_trap_line"),
					html.H3("Heatmap Results (Trapezoid)", className="results-title"),
					html.Div(dcc.Loading(dcc.Graph(id="trap_heat_fig", config={
						"displayModeBar": True,
						"scrollZoom": True,
						"doubleClick": "reset",
						"modeBarButtonsToRemove": [
							"pan2d", "zoom2d", "select2d", "lasso2d", "autoScale2d", "toggleSpikelines"
						]
					})), className="graph-container"),
					html.Button("Download Heatmap CSV (Trap)", id="btn_dl_trap_heat"),
				],
				className="results-section",
			),
		],
		className="main-content",
	)

	trapezoid_tab = dcc.Tab(label="Trapezoidal Load", value="tab-trap", children=[
		html.Div([side_trap, results_trap], className="container")
	])

	tabs = dcc.Tabs(id="tabs", value="tab-strip", children=[strip_tab, circle_tab, trapezoid_tab])

	# Theme settings modal
	modal = html.Div(
		[
			html.Div(
				[
					html.Button("×", id="close-modal", className="close-btn"),
					html.H3("Theme Settings", className="modal-title"),
					html.Div(
						[
							html.Div("Choose Color Palette:", className="theme-label"),
							html.Div(
								[
									# Light themes
									html.Div("Ocean Blue", id="theme-blue", className="theme-option active", **{"data-theme": "blue"}),
									html.Div("Royal Purple", id="theme-purple", className="theme-option", **{"data-theme": "purple"}),
									html.Div("Forest Green", id="theme-green", className="theme-option", **{"data-theme": "green"}),
									html.Div("Sunset Orange", id="theme-orange", className="theme-option", **{"data-theme": "orange"}),
									html.Div("Rose Pink", id="theme-pink", className="theme-option", **{"data-theme": "pink"}),
									# Dark themes
									html.Div("Dark Blue", id="theme-dark", className="theme-option", **{"data-theme": "dark"}),
									html.Div("Midnight Purple", id="theme-midnight", className="theme-option", **{"data-theme": "midnight"}),
									html.Div("Dark Forest", id="theme-forest", className="theme-option", **{"data-theme": "forest"}),
									html.Div("Crimson Night", id="theme-crimson", className="theme-option", **{"data-theme": "crimson"}),
									html.Div("Ocean Deep", id="theme-ocean", className="theme-option", **{"data-theme": "ocean"}),
									html.Div("Sunset Dark", id="theme-sunset", className="theme-option", **{"data-theme": "sunset"}),
								],
								className="theme-grid"
							),
						],
						className="modal-content"
					),
				],
				className="modal-inner"
			)
		],
		id="theme-modal",
		className="modal-overlay",
		style={"display": "none"}
	)

	return html.Div([header, tabs, modal], id="app-container", **{"data-theme": "blue"})


app.layout = make_layout()


# ---------- Callbacks (strip) ----------
@app.callback(
	Output("line_fig", "figure"),
	Output("line_store", "data"),
	Input("btn_line", "n_clicks"),
	Input("line_component", "value"),
	State("q", "value"),
	State("poisson_ratio", "value"),
	State("width_b", "value"),
	State("x0", "value"),
	State("y0", "value"),
	State("angle", "value"),
	State("lx0", "value"),
	State("ly0", "value"),
	State("lz0", "value"),
	State("lx1", "value"),
	State("ly1", "value"),
	State("lz1", "value"),
	prevent_initial_call=True,
)

def update_line_fig(
	_n_clicks: int,	line_component: str,
	q: float,
	poisson_ratio: float,
	B: float,
	x0: float,
	y0: float,
	angle: float,
	lx0: float,
	ly0: float,
	lz0: float,
	lx1: float,
	ly1: float,
	lz1: float,
):
	points = generate_line_points([lx0, ly0, lz0], [lx1, ly1, lz1], 200)
	# Analytical stresses
	sig_z, sig_x, sig_y, tau_xz = sigma_z_infinite_strip(
		points,
		width_b=B,
		uniform_pressure_q=q,
		poisson_ratio=poisson_ratio,
		rotation_deg=angle,
		center_xy=(x0, y0)
	)
	# distance along the line for x-axis
	dists = np.linalg.norm(points - points[0], axis=1)

	# Select component
	series_map = {
		"sigma_z": (sig_z, "σz"),
		"sigma_x": (sig_x, "σx"),
		"sigma_y": (sig_y, "σy"),
		"tau_xz": (tau_xz, "τxz"),
	}
	y_vals, label = series_map.get(line_component, (sig_z, "σz"))

	fig = go.Figure()
	fig.add_trace(
		go.Scatter(x=dists, y=y_vals, mode="lines", name=label,
			hovertemplate="s=%{x:.2f}, " + label + "=%{y:.3f}<extra></extra>")
	)
	fig.update_layout(
		template="plotly_white",
		title=f"{label} along 3D path",
		xaxis_title="Path length s",
		yaxis_title=f"{label} (same units as q)",
		font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
		margin=dict(l=60, r=20, t=50, b=50),
		height=420,
		hovermode="x unified",
		plot_bgcolor="#ffffff",
		paper_bgcolor="#ffffff",
		showlegend=False,
		dragmode="pan",
		xaxis=dict(constrain="domain"),
		yaxis=dict(constrain="domain"),
	)
	# Remove draw tools from modebar

	data = {
        "s": dists.tolist(),
        "x": points[:, 0].tolist(),
        "y": points[:, 1].tolist(),
        "z": points[:, 2].tolist(),
        "sigma_z": sig_z.tolist(),
        "sigma_x": sig_x.tolist(),
        "sigma_y": sig_y.tolist(),
        "tau_xz": tau_xz.tolist(),
    }
	return fig, data


@app.callback(
	Output("heat_fig", "figure"),
	Output("heat_store", "data"),
	Input("btn_heat", "n_clicks"),
	Input("heat_component", "value"),
	Input("heat_display", "value"),
	State("n_isobars", "value"),
	State("q", "value"),
	State("poisson_ratio", "value"),
	State("width_b", "value"),
	State("x0", "value"),
	State("y0", "value"),
	State("angle", "value"),
	State("plane", "value"),
	State("const_val", "value"),
	State("xmin", "value"),
	State("xmax", "value"),
	State("ymin", "value"),
	State("ymax", "value"),
	State("zmin", "value"),
	State("zmax", "value"),
	State("nx", "value"),
	State("ny", "value"),
	prevent_initial_call=True,
)

def update_heat_fig(
	_n_clicks: int,	heat_component: str, heat_display: str,
	n_isobars: int,
	q: float,
	poisson_ratio: float,
	B: float,
	x0: float,
	y0: float,
	angle: float,
	plane: str,
	const_val: float,
	xmin: float,
	xmax: float,
	ymin: float,
	ymax: float,
	zmin: float,
	zmax: float,
	nx: int,
	ny: int,
):
	plane = plane.lower()
	if plane == "xy":
		X, Y, Z = generate_plane_grid("xy", const_val, (xmin, xmax), (ymin, ymax), int(nx), int(ny))
	elif plane == "xz":
		X, Y, Z = generate_plane_grid("xz", const_val, (xmin, xmax), (zmin, zmax), int(nx), int(ny), z_bounds=(zmin, zmax))
	else:
		# For 'yz': third arg is x_bounds (unused), fourth is y_bounds
		X, Y, Z = generate_plane_grid("yz", const_val, (0, 0), (ymin, ymax), int(nx), int(ny), z_bounds=(zmin, zmax))

	pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
	# Get all stress components
	sig_z, sig_x, sig_y, tau_xz = sigma_z_infinite_strip(
		pts,
		width_b=B,
		uniform_pressure_q=q,
		poisson_ratio=poisson_ratio,
		rotation_deg=angle,
		center_xy=(x0, y0)
	)

	# Select component
	series_map = {
		"sigma_z": (sig_z, "σz"),
		"sigma_x": (sig_x, "σx"),
		"sigma_y": (sig_y, "σy"),
		"tau_xz": (tau_xz, "τxz"),
	}
	arr, label = series_map.get(heat_component, (sig_z, "σz"))
	S = arr.reshape(X.shape)

	if plane == "xy":
		x_vals = X[0, :]
		y_vals = Y[:, 0]
		layout = dict(xaxis_title="x", yaxis_title="y", title=f"{label} on XY plane at z={const_val}")
	elif plane == "xz":
		x_vals = X[0, :]
		y_vals = Z[:, 0]
		layout = dict(xaxis_title="x", yaxis_title="z", title=f"{label} on XZ plane at y={const_val}")
	else:
		x_vals = Y[0, :]
		y_vals = Z[:, 0]
		layout = dict(xaxis_title="y", yaxis_title="z", title=f"{label} on YZ plane at x={const_val}")

	if heat_display == "isobar":
		try:
			nc = int(n_isobars) if n_isobars and int(n_isobars) > 0 else 15
		except Exception:
			nc = 15
		trace = go.Contour(x=x_vals, y=y_vals, z=S, ncontours=nc, contours=dict(coloring="lines", showlabels=True, labelfont=dict(size=10, color="black")), line=dict(width=1.2, color="black"), showscale=False, name=label)
	else:
		trace = go.Heatmap(x=x_vals, y=y_vals, z=S, colorscale="Viridis", colorbar_title=label)

	fig = go.Figure(data=[trace])
	# Show z=0 at top and deeper z at bottom for XZ and YZ
	yaxis_settings = dict(constrain="domain")
	if plane in ("xz", "yz"):
		yaxis_settings["autorange"] = "reversed"
	fig.update_layout(
		template="plotly_white",
		font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
		margin=dict(l=60, r=20, t=50, b=50),
		height=520,
		hovermode="closest",
		plot_bgcolor="#ffffff",
		paper_bgcolor="#ffffff",
		dragmode="pan",
		xaxis=dict(constrain="domain"),
		yaxis=yaxis_settings,
		**layout,
	)
	# Remove draw tools from modebar

	data = {
		"plane": plane,
		"x": pts[:, 0].tolist(),
		"y": pts[:, 1].tolist(),
		"z": pts[:, 2].tolist(),
		"sigma_z": sig_z.tolist(),
		"sigma_x": sig_x.tolist(),
		"sigma_y": sig_y.tolist(),
		"tau_xz": tau_xz.tolist(),
		"shape": list(X.shape),
	}
	return fig, data


# ---------- Callbacks (circle) ----------
@app.callback(
	Output("line_fig_c", "figure"),
	Output("line_store_c", "data"),
	Input("btn_line_c", "n_clicks"),
	State("q_c", "value"),
	State("radius_a", "value"),
	State("x0_c", "value"),
	State("y0_c", "value"),
	State("lx0_c", "value"),
	State("ly0_c", "value"),
	State("lz0_c", "value"),
	State("lx1_c", "value"),
	State("ly1_c", "value"),
	State("lz1_c", "value"),
	State("line_component_c", "value"),
	prevent_initial_call=True,
)

def update_line_fig_c(
	_n_clicks: int,
	q: float,
	a: float,
	x0: float,
	y0: float,
	lx0: float,
	ly0: float,
	lz0: float,
	lx1: float,
	ly1: float,
	lz1: float,
	line_component: str,
):
	points = generate_line_points([lx0, ly0, lz0], [lx1, ly1, lz1], 200)
	# Compute stresses (sigma_r and sigma_theta removed)
	sig_z, tau_rz = integrate_circular_stress_full(points, radius_a=a, uniform_pressure_q=q, center_xy=(x0, y0))
	dists = np.linalg.norm(points - points[0], axis=1)
	series_map = {
		"sigma_z": (sig_z, "σz"),
		"tau_rz": (tau_rz, "τrz"),
	}
	y_vals, label = series_map.get(line_component, (sig_z, "σz"))
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=dists, y=y_vals, mode="lines", name=label))
	fig.update_layout(template="plotly_white", title=f"{label} along 3D path (Circular)", xaxis_title="Path length s", yaxis_title=label)
	# Remove draw tools from modebar
	data = {
		"s": dists.tolist(),
		"x": points[:, 0].tolist(),
		"y": points[:, 1].tolist(),
		"z": points[:, 2].tolist(),
		"sigma_z": sig_z.tolist(),
		"tau_rz": tau_rz.tolist(),
	}
	return fig, data


@app.callback(
	Output("heat_fig_c", "figure"),
	Output("heat_store_c", "data"),
	Input("btn_heat_c", "n_clicks"),
	Input("heat_display_c", "value"),
	State("n_isobars_c", "value"),
    State("q_c", "value"),
	State("radius_a", "value"),
	State("x0_c", "value"),
	State("y0_c", "value"),
	State("plane_c", "value"),
	State("const_val_c", "value"),
	State("xmin_c", "value"),
	State("xmax_c", "value"),
	State("ymin_c", "value"),
	State("ymax_c", "value"),
	State("zmin_c", "value"),
	State("zmax_c", "value"),
	State("nx_c", "value"),
	State("ny_c", "value"),
	State("heat_component_c", "value"),
	prevent_initial_call=True,
)

def update_heat_fig_c(
	_n_clicks: int, heat_display: str,
	n_isobars_c: int,
	q: float,
	a: float,
	x0: float,
	y0: float,
	plane: str,
	const_val: float,
	xmin: float,
	xmax: float,
	ymin: float,
	ymax: float,
	zmin: float,
	zmax: float,
	nx: int,
	ny: int,
	heat_component: str,
):
	plane = plane.lower()
	if plane == "xy":
		X, Y, Z = generate_plane_grid("xy", const_val, (xmin, xmax), (ymin, ymax), int(nx), int(ny))
	elif plane == "xz":
		X, Y, Z = generate_plane_grid("xz", const_val, (xmin, xmax), (zmin, zmax), int(nx), int(ny), z_bounds=(zmin, zmax))
	else:
		# For 'yz': third arg is x_bounds (unused), fourth is y_bounds
		X, Y, Z = generate_plane_grid("yz", const_val, (0, 0), (ymin, ymax), int(nx), int(ny), z_bounds=(zmin, zmax))

	pts = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])
	# Compute stresses (sigma_r and sigma_theta removed)
	sig_z, tau_rz = integrate_circular_stress_full(pts, radius_a=a, uniform_pressure_q=q, center_xy=(x0, y0))
	series_map = {
		"sigma_z": (sig_z, "σz"),
		"tau_rz": (tau_rz, "τrz"),
	}
	arr, label = series_map.get(heat_component, (sig_z, "σz"))
	S = arr.reshape(X.shape)

	if plane == "xy":
		x_vals = X[0, :]
		y_vals = Y[:, 0]
		layout = dict(xaxis_title="x", yaxis_title="y", title=f"{label} on XY plane at z={const_val}")
	elif plane == "xz":
		x_vals = X[0, :]
		y_vals = Z[:, 0]
		layout = dict(xaxis_title="x", yaxis_title="z", title=f"{label} on XZ plane at y={const_val}")
	else:
		x_vals = Y[0, :]
		y_vals = Z[:, 0]
		layout = dict(xaxis_title="y", yaxis_title="z", title=f"{label} on YZ plane at x={const_val}")

	if heat_display == "isobar":
		try:
			nc = int(n_isobars_c) if n_isobars_c and int(n_isobars_c) > 0 else 15
		except Exception:
			nc = 15
		trace = go.Contour(x=x_vals, y=y_vals, z=S, ncontours=nc, contours=dict(coloring="lines", showlabels=True, labelfont=dict(size=10, color="black")), line=dict(width=1.2, color="black"), showscale=False, name=label)
	else:
		trace = go.Heatmap(x=x_vals, y=y_vals, z=S, colorscale="Viridis", colorbar_title=label)

	fig = go.Figure(data=[trace])
	# Show z=0 at top and deeper z at bottom for XZ and YZ
	yaxis_settings_c = dict(constrain="domain")
	if plane in ("xz", "yz"):
		yaxis_settings_c["autorange"] = "reversed"
	fig.update_layout(
		template="plotly_white",
		font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
		margin=dict(l=60, r=20, t=50, b=50),
		height=520,
		hovermode="closest",
		plot_bgcolor="#ffffff",
		paper_bgcolor="#ffffff",
		xaxis=dict(constrain="domain"),
		yaxis=yaxis_settings_c,
		dragmode="pan",
		**layout,
	)
	data = {
		"plane": plane,
		"x": pts[:, 0].tolist(),
		"y": pts[:, 1].tolist(),
		"z": pts[:, 2].tolist(),
		"sigma_z": sig_z.tolist(),
		"tau_rz": tau_rz.tolist(),
		"shape": list(X.shape),
	}
	return fig, data


# ---------- Callback (trapezoidal load) ----------
@app.callback(
	Output("trap_line_fig", "figure"),
	Output("trap_line_store", "data"),
	Input("btn_trap_line", "n_clicks"),
	State("trap_a1", "value"),
	State("trap_a2", "value"),
	State("trap_b", "value"),
	State("trap_q", "value"),
	State("trap_lx0", "value"),
	State("trap_ly0", "value"),
	State("trap_lz0", "value"),
	State("trap_lx1", "value"),
	State("trap_ly1", "value"),
	State("trap_lz1", "value"),
	prevent_initial_call=True,
)
def update_trap_line_fig(_n_clicks: int, a1: float, a2: float, b: float, q: float,
	lx0: float, ly0: float, lz0: float, lx1: float, ly1: float, lz1: float):
	if not _n_clicks:
		raise PreventUpdate
	points = generate_line_points([lx0, ly0, lz0], [lx1, ly1, lz1], 200)
	x = points[:, 0]
	z = points[:, 2]
	# Avoid division by zero for z
	z_safe = np.where(z == 0, np.finfo(float).eps, z)
	# Angles using arctan differences (safe z denominator)
	alpha1 = np.arctan(((-b) - x) / z_safe) - np.arctan(((-a1 - b) - x) / z_safe)
	alpha2 = np.arctan(( b   - x) / z_safe) - np.arctan(((-b)      - x) / z_safe)
	alpha3 = np.arctan(((b+a2) - x) / z_safe) - np.arctan(( b       - x) / z_safe)
	# sigma_z expression; guard a1,a2
	a1_safe = a1 if a1 != 0 else np.finfo(float).eps
	a2_safe = a2 if a2 != 0 else np.finfo(float).eps
	term = (alpha1 + alpha2 + alpha3) \
		+ (b / a1_safe) * (alpha1 + (a1_safe * alpha3 / a2_safe)) \
		+ (x / a1_safe) * (alpha1 - (a1_safe * alpha3 / a2_safe))
	sig_z = (q / math.pi) * term
	# Distance along line
	dists = np.linalg.norm(points - points[0], axis=1)
	fig = go.Figure()
	fig.add_trace(go.Scatter(x=dists, y=sig_z, mode="lines", name="σz"))
	fig.update_layout(
		template="plotly_white",
		title="σz along 3D path (Trapezoid)",
		xaxis_title="Path length s",
		yaxis_title="σz (units of q)",
		font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
		margin=dict(l=60, r=20, t=50, b=50),
		height=420,
		hovermode="x unified",
		plot_bgcolor="#ffffff",
		paper_bgcolor="#ffffff",
		showlegend=False,
		dragmode="pan",
		xaxis=dict(constrain="domain"),
		yaxis=dict(constrain="domain"),
	)
	data = {
		"s": dists.tolist(),
		"x": points[:, 0].tolist(),
		"y": points[:, 1].tolist(),
		"z": points[:, 2].tolist(),
		"sigma_z": sig_z.tolist(),
	}
	return fig, data


@app.callback(
	Output("trap_heat_fig", "figure"),
	Output("trap_heat_store", "data"),
	Input("btn_trap_heat", "n_clicks"),
	State("trap_a1", "value"),
	State("trap_a2", "value"),
	State("trap_b", "value"),
	State("trap_q", "value"),
	State("trap_xmin", "value"),
	State("trap_xmax", "value"),
	State("trap_zmin", "value"),
	State("trap_zmax", "value"),
	State("trap_nx", "value"),
	State("trap_nz", "value"),
	State("trap_heat_display", "value"),
	State("trap_n_isobars", "value"),
	prevent_initial_call=True,
)
def update_trap_heat_fig(_n_clicks: int, a1: float, a2: float, b: float, q: float,
	xmin: float, xmax: float, zmin: float, zmax: float, nx: int, nz: int, heat_display: str, trap_n_isobars: int):
	if not _n_clicks:
		raise PreventUpdate
	# Create XZ grid at y=0 to match plane strain slice
	x_vals = np.linspace(xmin, xmax, int(nx))
	z_vals = np.linspace(zmin, zmax, int(nz))
	X, Z = np.meshgrid(x_vals, z_vals)
	Z_safe = np.where(Z == 0, np.finfo(float).eps, Z)
	alpha1 = np.arctan(((-b) - X) / Z_safe) - np.arctan(((-a1 - b) - X) / Z_safe)
	alpha2 = np.arctan(( b   - X) / Z_safe) - np.arctan(((-b)      - X) / Z_safe)
	alpha3 = np.arctan(((b+a2) - X) / Z_safe) - np.arctan(( b       - X) / Z_safe)
	a1_safe = a1 if a1 != 0 else np.finfo(float).eps
	a2_safe = a2 if a2 != 0 else np.finfo(float).eps
	term = (alpha1 + alpha2 + alpha3) \
		+ (b / a1_safe) * (alpha1 + (a1_safe * alpha3 / a2_safe)) \
		+ ((X) / a1_safe) * (alpha1 - (a1_safe * alpha3 / a2_safe))
	S = (q / math.pi) * term
	if heat_display == "isobar":
		try:
			nc = int(trap_n_isobars) if trap_n_isobars and int(trap_n_isobars) > 0 else 15
		except Exception:
			nc = 15
		trace = go.Contour(x=x_vals, y=z_vals, z=S, ncontours=nc, contours=dict(coloring="lines", showlabels=True, labelfont=dict(size=10, color="black")), line=dict(width=1.2, color="black"), showscale=False, name="σz")
	else:
		trace = go.Heatmap(x=x_vals, y=z_vals, z=S, colorscale="Viridis", colorbar_title="σz")
	fig = go.Figure(data=[trace])
	fig.update_layout(
		template="plotly_white",
		font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
		margin=dict(l=60, r=20, t=50, b=50),
		height=520,
		hovermode="closest",
		plot_bgcolor="#ffffff",
		paper_bgcolor="#ffffff",
		dragmode="pan",
		xaxis=dict(title="x", constrain="domain"),
		yaxis=dict(title="z", constrain="domain", autorange="reversed"),
	)
	data = {
		"x": X.ravel().tolist(),
		"z": Z.ravel().tolist(),
		"sigma_z": S.ravel().tolist(),
		"shape": list(X.shape),
	}
	return fig, data


@app.callback(
	Output("download_trap_line", "data"),
	Input("btn_dl_trap_line", "n_clicks"),
	State("trap_line_store", "data"),
	prevent_initial_call=True,
)
def download_trap_line_csv(n_clicks: int, data: dict):
	if not n_clicks or not data:
		raise PreventUpdate
	buf = io.StringIO()
	buf.write("s,x,y,z,sigma_z\n")
	for s, x, y, z, sz in zip(data["s"], data["x"], data["y"], data["z"], data["sigma_z"]):
		buf.write(f"{s},{x},{y},{z},{sz}\n")
	return dcc.send_string(buf.getvalue(), "trap_line_profile.csv")


@app.callback(
	Output("download_trap_heat", "data"),
	Input("btn_dl_trap_heat", "n_clicks"),
	State("trap_heat_store", "data"),
	prevent_initial_call=True,
)
def download_trap_heat_csv(n_clicks: int, data: dict):
	if not n_clicks or not data:
		raise PreventUpdate
	buf = io.StringIO()
	buf.write("x,z,sigma_z\n")
	for x, z, sz in zip(data["x"], data["z"], data["sigma_z"]):
		buf.write(f"{x},{z},{sz}\n")
	return dcc.send_string(buf.getvalue(), "trap_heatmap_points.csv")


@app.callback(
    Output("download_line", "data"),
    Input("btn_dl_line", "n_clicks"),
    State("line_store", "data"),
    prevent_initial_call=True,
)
def download_line_csv(n_clicks: int, data: dict):
    if not n_clicks or not data:
        raise PreventUpdate
    buf = io.StringIO()
    buf.write("s,x,y,z,sigma_z,sigma_x,sigma_y,tau_xz\n")
    for s, x, y, z, sz, sx, sy, txz in zip(data["s"], data["x"], data["y"], data["z"], data["sigma_z"], data["sigma_x"], data["sigma_y"], data["tau_xz"]):
        buf.write(f"{s},{x},{y},{z},{sz},{sx},{sy},{txz}\n")
    return dcc.send_string(buf.getvalue(), "line_profile.csv")


@app.callback(
    Output("download_heat", "data"),
    Input("btn_dl_heat", "n_clicks"),
    State("heat_store", "data"),
    prevent_initial_call=True,
)
def download_heat_csv(n_clicks: int, data: dict):
    if not n_clicks or not data:
        raise PreventUpdate
    buf = io.StringIO()
    buf.write("x,y,z,sigma_z,sigma_x,sigma_y,tau_xz\n")
    for x, y, z, sz, sx, sy, txz in zip(data["x"], data["y"], data["z"], data["sigma_z"], data["sigma_x"], data["sigma_y"], data["tau_xz"]):
        buf.write(f"{x},{y},{z},{sz},{sx},{sy},{txz}\n")
    return dcc.send_string(buf.getvalue(), "heatmap_points.csv")


@app.callback(
    Output("download_line_c", "data"),
    Input("btn_dl_line_c", "n_clicks"),
    State("line_store_c", "data"),
    prevent_initial_call=True,
)
def download_line_csv_circle(n_clicks: int, data: dict):
    if not n_clicks or not data:
        raise PreventUpdate
    buf = io.StringIO()
    # Include available circular components (sigma_r and sigma_theta removed)
    buf.write("s,x,y,z,sigma_z,tau_rz\n")
    for s, x, y, z, sz, trz in zip(
        data["s"], data["x"], data["y"], data["z"],
        data["sigma_z"], data["tau_rz"]
    ):
        buf.write(f"{s},{x},{y},{z},{sz},{trz}\n")
    return dcc.send_string(buf.getvalue(), "circle_line_profile.csv")


@app.callback(
    Output("download_heat_c", "data"),
    Input("btn_dl_heat_c", "n_clicks"),
    State("heat_store_c", "data"),
    prevent_initial_call=True,
)
def download_heat_csv_circle(n_clicks: int, data: dict):
    if not n_clicks or not data:
        raise PreventUpdate
    buf = io.StringIO()
    buf.write("x,y,z,sigma_z,tau_rz\n")
    for x, y, z, sz, trz in zip(
        data["x"], data["y"], data["z"],
        data["sigma_z"], data["tau_rz"]
    ):
        buf.write(f"{x},{y},{z},{sz},{trz}\n")
    return dcc.send_string(buf.getvalue(), "circle_heatmap_points.csv")


# Theme and modal callbacks
@app.callback(
	Output("theme-modal", "style"),
	Input("settings-btn", "n_clicks"),
	Input("close-modal", "n_clicks"),
	prevent_initial_call=True
)
def toggle_modal(settings_clicks, close_clicks):
	if not ctx.triggered:
		return {"display": "none"}
	
	button_id = ctx.triggered[0]["prop_id"].split(".")[0]
	if button_id == "settings-btn":
		return {"display": "flex"}
	else:
		return {"display": "none"}


@app.callback(
	[Output("app-container", "data-theme"),
	 Output("theme-blue", "className"),
	 Output("theme-purple", "className"),
	 Output("theme-green", "className"),
	 Output("theme-orange", "className"),
	 Output("theme-pink", "className"),
	 Output("theme-dark", "className"),
	 Output("theme-midnight", "className"),
	 Output("theme-forest", "className"),
	 Output("theme-crimson", "className"),
	 Output("theme-ocean", "className"),
	 Output("theme-sunset", "className")],
	[Input("theme-blue", "n_clicks"),
	 Input("theme-purple", "n_clicks"),
	 Input("theme-green", "n_clicks"),
	 Input("theme-orange", "n_clicks"),
	 Input("theme-pink", "n_clicks"),
	 Input("theme-dark", "n_clicks"),
	 Input("theme-midnight", "n_clicks"),
	 Input("theme-forest", "n_clicks"),
	 Input("theme-crimson", "n_clicks"),
	 Input("theme-ocean", "n_clicks"),
	 Input("theme-sunset", "n_clicks")],
	prevent_initial_call=True
)
def update_theme(*clicks):
	if not ctx.triggered:
		return ("blue", "theme-option active") + ("theme-option",) * 10
	
	button_id = ctx.triggered[0]["prop_id"].split(".")[0]
	theme_map = {
		"theme-blue": "blue",
		"theme-purple": "purple", 
		"theme-green": "green",
		"theme-orange": "orange",
		"theme-pink": "pink",
		"theme-dark": "dark",
		"theme-midnight": "midnight",
		"theme-forest": "forest",
		"theme-crimson": "crimson",
		"theme-ocean": "ocean",
		"theme-sunset": "sunset"
	}
	
	selected_theme = theme_map.get(button_id, "blue")
	
	# Update class names
	theme_ids = ["theme-blue", "theme-purple", "theme-green", "theme-orange", "theme-pink",
	             "theme-dark", "theme-midnight", "theme-forest", "theme-crimson", "theme-ocean", "theme-sunset"]
	classes = []
	for theme_id in theme_ids:
		if theme_id == button_id:
			classes.append("theme-option active")
		else:
			classes.append("theme-option")
	
	return selected_theme, *classes


if __name__ == "__main__":
	app.run(debug=True, dev_tools_hot_reload=False, dev_tools_ui=False)

