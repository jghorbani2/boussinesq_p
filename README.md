# Boussinesq Stress Analysis Web Application

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.17.1-green.svg)](https://dash.plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An interactive web application for computing and visualizing stress distributions under loaded foundations using the Boussinesq solution. The app supports three foundation types: strip footings, circular footings, and trapezoidal loads.


## 🚀 Features

### Foundation Types
- **Strip Footing**: Infinite strip with analytical solution for all stress components (σz, σx, σy, τxz)
- **Circular Footing**: Circular foundation with numerical integration (σz, τrz)
- **Trapezoidal Load**: Plane strain trapezoidal loading (σz)

### Visualization Options
- **Line Plots**: Stress profiles along arbitrary 3D paths
- **Heatmaps**: 2D stress distributions on plane slices (XY, XZ, YZ)
- **Contour Plots**: Isobar visualization with customizable contour levels
- **Interactive Controls**: Zoom, pan, hover data, and export capabilities

### Advanced Features
- Foundation rotation and translation
- Multiple stress components
- Customizable grid resolution
- Adjustable isobar count for contour plots
- CSV data export
- Multiple color themes
- Responsive design

## 📋 Theory

The application implements the Boussinesq solution for elastic half-space problems. For a point load P at position (ξ, η, 0), the vertical stress at point (x, y, z) is:

```
σz = (3P/2π) × z³/r⁵
```

where `r² = (x-ξ)² + (y-η)² + z²`

For distributed loads, the stress is computed by integrating the point load solution over the loaded area:

```
σz(x,y,z) = q ∬ [3z³/2π × 1/((x-ξ)²+(y-η)²+z²)^(5/2)] dξ dη
```

### Implementation Methods

1. **Strip Footing**: Analytical solution using arctangent functions
2. **Circular Footing**: Numerical integration using Simpson's rule in polar coordinates
3. **Trapezoidal Load**: Analytical solution for plane strain conditions

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or download the repository**:
```bash
git clone <repository-url>
cd bous
```

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the application**:
```bash
python app.py
```

5. **Open your browser** and navigate to:
```
http://127.0.0.1:8050
```

### Alternative Installation Methods

#### Using conda
```bash
conda create -n bous python=3.9
conda activate bous
pip install -r requirements.txt
python app.py
```

#### Docker (if Dockerfile available)
```bash
docker build -t bous-app .
docker run -p 8050:8050 bous-app
```

## 📦 Dependencies

The application requires the following Python packages:

- `dash==2.17.1` - Web application framework
- `plotly==5.22.0` - Interactive plotting library
- `numpy>=1.24.0` - Numerical computations
- `gunicorn>=21.2.0` - WSGI server for production (optional)

## 🎯 Usage Guide

### Strip Footing Analysis

1. **Configure Foundation**:
   - Set uniform pressure q (kPa)
   - Define width B (m)
   - Set Poisson's ratio ν
   - Position using center coordinates (x₀, y₀)
   - Apply rotation angle (degrees)

2. **Line Analysis**:
   - Define start and end points for 3D path
   - Select stress component (σz, σx, σy, τxz)
   - Click "Compute Line Plot"

3. **Heatmap Analysis**:
   - Choose plane type (XY, XZ, YZ)
   - Set plane position (constant value)
   - Define analysis bounds and grid resolution
   - Select stress component and display type
   - Adjust isobar count for contour plots
   - Click "Compute Heatmap"

### Circular Footing Analysis

1. **Configure Foundation**:
   - Set uniform pressure q (kPa)
   - Define radius a (m)
   - Position using center coordinates (x₀, y₀)

2. **Analysis Options**:
   - Available stress components: σz, τrz
   - Same plane and visualization options as strip footing

### Trapezoidal Load Analysis

1. **Configure Geometry**:
   - Set dimensions a₁, a₂, b (m)
   - Define uniform pressure q (kPa)

2. **Analysis**:
   - Line plots along arbitrary 3D paths
   - XZ plane heatmaps only
   - Stress component: σz

## 📊 Output and Export

### Interactive Features
- **Zoom and Pan**: Navigate through plots
- **Hover Data**: View precise values
- **Legend Toggle**: Show/hide plot elements

### Data Export
- **CSV Export**: Download raw data for all analyses
- **Image Export**: Save plots as PNG/PDF (via browser)
- **Data Format**: Organized with coordinates and stress values

### File Formats
- Line data: `s, x, y, z, stress_components`
- Heatmap data: `x, y, z, stress_components`

## 🎨 Customization

### Themes
The application includes multiple color themes:
- Light themes: Ocean Blue, Royal Purple, Forest Green, Sunset Orange, Rose Pink
- Dark themes: Dark Blue, Midnight Purple, Dark Forest, Crimson Night, Ocean Deep, Sunset Dark

### Plot Settings
- Adjustable grid resolution (higher = more detailed, slower computation)
- Customizable isobar count (1-200 contours)
- Flexible coordinate ranges

## ⚡ Performance Notes

### Computational Efficiency
- **Strip Footing**: Analytical solution - very fast
- **Circular Footing**: Numerical integration - moderate speed
- **Trapezoidal Load**: Analytical solution - fast

### Memory Management
- Automatic batching for large grids
- Adaptive integration resolution
- Optimized for interactive use

### Recommended Settings
- Grid resolution: 80-120 for interactive use, up to 200 for publication
- Isobar count: 10-20 for clarity, up to 50 for detailed analysis

## 🔧 Troubleshooting

### Common Issues

1. **Application won't start**:
   - Check Python version (3.8+)
   - Verify all dependencies are installed
   - Try recreating virtual environment

2. **Slow performance**:
   - Reduce grid resolution
   - Lower isobar count
   - Use smaller analysis domains

3. **Memory errors**:
   - Reduce grid size
   - Close other applications
   - Consider using smaller analysis regions

4. **Plotting issues**:
   - Update browser
   - Clear browser cache
   - Check JavaScript console for errors

### Getting Help
- Check the console output for error messages
- Verify input parameters are within reasonable ranges
- Ensure coordinate system consistency (z ≥ 0)

## 📚 Technical Details

### Coordinate System
- **X, Y**: Horizontal coordinates (m)
- **Z**: Depth, positive downward from surface (m)
- **Surface**: z = 0
- **Units**: Consistent throughout (if q in kPa and lengths in m, stresses in kPa)

### Numerical Methods
- **Analytical strip solution**: Closed-form arctangent-based expressions (plane strain, infinite strip)
- **Simpson's Rule (polar)**: For circular footing integration over the loaded disk
- **Analytical trapezoid formula**: Plane-strain closed form for σz on the XZ slice
- **Adaptive resolution/batching**: Automatically adjusts nodes and batch sizes for large grids

### Accuracy Considerations
- Strip footing: Exact analytical solution
- Circular footing: High accuracy with adaptive integration
- Surface boundary conditions properly enforced
- Singularity handling at z = 0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Performance optimizations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Based on Boussinesq's classical elasticity theory
- Implements modern numerical methods for practical engineering applications
- Built with Dash and Plotly for interactive visualization

## 📞 Support

For questions, issues, or feature requests, please open an issue on the project repository.

---

**Note**: This application is designed for educational and engineering analysis purposes. For critical structural design, always verify results with established methods and consult relevant design codes.

## ☁️ Deploy to Google Cloud Run

### Prerequisites
- Google Cloud project with billing enabled
- Google Cloud SDK installed and authenticated
- Set your project and region:
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region YOUR_REGION   # e.g., us-central1
```

### Build and Deploy
```bash
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/boussinesq-app
gcloud run deploy boussinesq-app \
  --image gcr.io/$(gcloud config get-value project)/boussinesq-app \
  --platform managed \
  --allow-unauthenticated \
  --port 8080
```

The container runs `gunicorn app:server` and listens on `$PORT` (Cloud Run sets it). Cloud Run outputs the public URL on success.