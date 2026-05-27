# NIST Gas Viscosity Extractor

A Python utility for automatically extracting high-pressure, high-temperature (HPHT) gas viscosity data from the NIST Chemistry WebBook. This tool compiles viscosity data for **methane** and **nitrogen** across a comprehensive range of pressure and temperature conditions suitable for machine learning applications.

**Project Context:** B.Eng Final Year Project  
**Institution:** University of Port Harcourt, Department of Gas Engineering  
**Author:** Prince Clarence Akpan (U2020/3070033)

---

## Overview

This project was developed to support the training of machine learning models for predicting gas viscosity under HPHT conditions. The extractor queries the NIST Chemistry WebBook API to retrieve experimentally validated viscosity data, then processes and consolidates it into structured CSV files for downstream analysis.

### Key Features

- **Automated Data Collection**: Fetches data directly from NIST's public Chemistry WebBook
- **HPHT Coverage**: Collects data across 26 pressure points (10–170 MPa) and 21 temperature points (300–700 K)
- **Dual Gas Support**: Extracts data for both pure methane (CH₄) and pure nitrogen (N₂)
- **Polite Web Scraping**: Implements 1-second delays between requests to avoid overloading NIST servers
- **Data Validation**: Removes invalid/non-physical values (e.g., negative viscosity)
- **Multiple Output Formats**: Generates both filtered and full-detail CSV files

---

## Data Specifications

### Pressure Range
- **Minimum**: 10 MPa (~1,450 psia)
- **Maximum**: 170 MPa (~24,656 psia)
- **HPHT Threshold**: >68.95 MPa (10,000 psia)
- **26 Total Pressure Points**: 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140, 150, 160, 170 MPa

### Temperature Range
- **Minimum**: 300 K (~80°F)
- **Maximum**: 700 K (~800°F)
- **HPHT Threshold**: >300°F (422 K)
- **21 Total Temperature Points**: 300, 320, 340, 360, 380, 400, 422, 440, 460, 480, 500, 520, 540, 560, 580, 600, 620, 640, 660, 680, 700 K

### Gas Composition
| Property | Methane | Nitrogen |
|----------|---------|----------|
| CAS ID | C74828 | C7727379 |
| Specific Gravity | 0.5539 | 0.9672 |
| CO₂ Fraction | 0.0 | 0.0 |
| N₂ Fraction | 0.0 | 1.0 |
| Pure | Yes | Yes |

### Output Data Points
- **Total Data Points**: 990 (up to 1,050 including all conditions)
- **Methane Points**: ~504
- **Nitrogen Points**: ~486
- **HPHT Subset**: ~350+ points (P > 10,000 psia, T > 300°F)

---

## Installation

### Prerequisites
- Python 3.7+
- Internet connection (for NIST WebBook access)

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Numba1ne/nist-gas-viscosity-extractor.git
   cd nist-gas-viscosity-extractor
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install requests>=2.28.0 pandas>=1.5.0
   ```

---

## Usage

### Running the Extractor

```bash
python nist_data_extractor.py
```

**Expected Runtime**: 3–5 minutes (includes 1-second delays between ~26 NIST API requests)

### Output Files

After successful execution, the following CSV files are generated:

#### 1. `gas_viscosity_data.csv` (Main Output)
**Purpose**: Ready-to-use dataset for machine learning models  
**Rows**: ~990 data points  
**Columns**:
- `Pressure_psia`: Pressure in pounds per square inch absolute
- `Temperature_F`: Temperature in Fahrenheit
- `Gas_SG`: Gas specific gravity (relative to air)
- `CO2_fraction`: Mole fraction of CO₂ (0.0 for pure gases)
- `N2_fraction`: Mole fraction of N₂ (1.0 for nitrogen, 0.0 for methane)
- `Viscosity_cp`: Dynamic viscosity in centipoise

**Example Rows**:
```
Pressure_psia,Temperature_F,Gas_SG,CO2_fraction,N2_fraction,Viscosity_cp
1450.4,80.3,0.5539,0.0,0.0,0.013753
1450.4,116.3,0.5539,0.0,0.0,0.014043
...
24656.5,656.3,0.9672,0.0,1.0,0.051776
```

#### 2. `methane_viscosity_nist.csv`
**Purpose**: Isolated methane data with extended properties  
**Rows**: ~504 data points  
**Includes**: Temperature (K), Pressure (MPa), Density, and viscosity in multiple units

#### 3. `nitrogen_viscosity_nist.csv`
**Purpose**: Isolated nitrogen data with extended properties  
**Rows**: ~486 data points  
**Includes**: Temperature (K), Pressure (MPa), Density, and viscosity in multiple units

#### 4. `gas_viscosity_data_full.csv` (Reference)
**Purpose**: Complete dataset with all derived properties  
**Extra Columns**: Temperature_K, Pressure_MPa, Density_kg_m3  
**Use Case**: Detailed analysis and property verification

---

## Data Format & Conversions

### Viscosity Units
- **NIST Output**: microPa·s (µPa·s)
- **Output Format**: Centipoise (cp)
- **Conversion**: 1 cp = 1,000 µPa·s

### Pressure Conversions
- 1 MPa = 145.038 psia
- 10,000 psia ≈ 68.95 MPa
- 25,000 psia ≈ 172.37 MPa

### Temperature Conversions
- Kelvin to Fahrenheit: °F = (K − 273.15) × 9/5 + 32
- Kelvin to Celsius: °C = K − 273.15

---

## Code Architecture

### Main Components

#### `fetch_nist_isobar(cas_id, temperature_low_k, temperature_high_k, pressure_mpa, gas_name)`
Fetches viscosity data from NIST WebBook for a single isobaric (constant pressure) line.

**Parameters**:
- `cas_id`: NIST Chemical Abstracts Service identifier
- `temperature_low_k`, `temperature_high_k`: Temperature range in Kelvin
- `pressure_mpa`: Pressure in MPa
- `gas_name`: Gas name for logging

**Returns**: Raw HTML response from NIST

#### `parse_nist_response(html_text)`
Parses NIST HTML response to extract tabular data.

**Returns**: List of dictionaries with parsed values (Temperature, Viscosity, Density, etc.)

#### `collect_gas_data(config)`
Main collection function that iterates through all P-T combinations for a single gas.

**Parameters**:
- `config`: Dictionary containing gas-specific parameters (name, CAS ID, composition)

**Returns**: List of consolidated data points with all unit conversions

#### `main()`
Orchestrates the full extraction workflow:
1. Collects methane data
2. Collects nitrogen data
3. Saves individual gas files
4. Combines data and creates model-ready output
5. Generates summary statistics

---

## Data Quality & Validation

### Quality Checks Implemented

1. **Non-null Viscosity**: Only records with valid viscosity values are retained
2. **Positive Values**: Non-physical negative viscosities are filtered out
3. **Precision Rounding**: Values rounded to appropriate decimal places:
   - Pressure: 1 decimal place (psia)
   - Temperature: 1 decimal place (°F, K)
   - Viscosity: 6 decimal places (cp)
   - Density: 4 decimal places (kg/m³)

### Summary Statistics

A typical run produces output like:
```
Total data points:     990
HPHT data points:      350+
Non-HPHT data points:  640
Methane points:        504
Nitrogen points:       486

Pressure range:  1450.4 - 24656.5 psia
Temp range:      80.3 - 800.3 F
Viscosity range: 0.013753 - 0.074502 cp
```

---

## Machine Learning Applications

### Recommended Use Cases

1. **Viscosity Prediction Models**:
   - Neural Networks (DNN)
   - Gradient Boosting (XGBoost, LightGBM)
   - Support Vector Regression (SVR)
   - Random Forest Regression

2. **Feature Engineering**:
   - Log-transform viscosity for normalized distribution
   - Pressure × Temperature interactions
   - Dimensionless groups (e.g., reduced properties)
   - Gas composition ratios

3. **Data Splitting**:
   - **Training**: Non-HPHT and lower-HPHT data (~640 points)
   - **Validation/Test**: HPHT data (~350 points)
   - Ensures model evaluation on critical high-pressure conditions

### Example Model Inputs
```python
import pandas as pd
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('gas_viscosity_data.csv')

# Define HPHT condition
hpht_mask = (df['Pressure_psia'] > 10000) & (df['Temperature_F'] > 300)

# Features and target
X = df[['Pressure_psia', 'Temperature_F', 'Gas_SG', 'CO2_fraction', 'N2_fraction']]
y = df['Viscosity_cp']

# Train on moderate conditions, validate on HPHT
X_train, X_test, y_train, y_test = train_test_split(
    X[~hpht_mask], y[~hpht_mask], test_size=0.2
)
# Use HPHT data for final evaluation
X_hpht, y_hpht = X[hpht_mask], y[hpht_mask]
```

---

## API Reference: NIST Chemistry WebBook

### Endpoint
```
https://webbook.nist.gov/cgi/fluid.cgi
```

### Parameters Used
| Parameter | Value | Purpose |
|-----------|-------|---------|
| `Action` | `Data` | Request data (not properties) |
| `Wide` | `on` | Wide output format |
| `ID` | CAS ID | Chemical identifier |
| `Type` | `IsoBar` | Constant pressure line |
| `Digits` | `5` | Decimal precision |
| `TUnit` | `K` | Temperature unit (Kelvin) |
| `PUnit` | `MPa` | Pressure unit (MPa) |
| `VisUnit` | `uPa*s` | Viscosity unit (microPa·s) |
| `THigh`, `TLow`, `TInc` | Variable | Temperature range & increment |

### Rate Limiting
- **Current Delay**: 1 second between requests
- **Rationale**: Respectful web scraping; prevents server overload
- **Future Optimization**: Implement exponential backoff for error handling

---

## Troubleshooting

### Issue: Script takes longer than expected
**Cause**: Network latency or NIST server slowness  
**Solution**: Increase `time.sleep()` delay or reduce temperature/pressure points

### Issue: Missing data points in output
**Cause**: NIST may not have data for certain P-T combinations  
**Solution**: Check NIST WebBook manually at https://webbook.nist.gov/chemistry/fluid/

### Issue: No data collected
**Cause**: Network connection lost or NIST unavailable  
**Solution**: 
1. Check internet connectivity
2. Try again after a few minutes
3. Visit NIST manually: https://webbook.nist.gov/chemistry/fluid/

### Issue: Invalid values in output
**Cause**: Parsing error or corrupted NIST response  
**Solution**: Manually download from NIST and validate; check for column header changes

---

## File Structure

```
nist-gas-viscosity-extractor/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── nist_data_extractor.py             # Main extraction script
├── .gitignore                         # Git ignore rules
├── gas_viscosity_data.csv             # ✓ Model-ready dataset (main output)
├── methane_viscosity_nist.csv         # ✓ Methane-only data
├── nitrogen_viscosity_nist.csv        # ✓ Nitrogen-only data
└── gas_viscosity_data_full.csv        # ✓ Full dataset with all properties
```

---

## Dependencies

### Core Requirements
- **requests** (≥2.28.0): HTTP library for NIST API queries
- **pandas** (≥1.5.0): Data manipulation and CSV I/O

### Optional (for downstream use)
- **numpy**: Numerical computations
- **scikit-learn**: Machine learning models
- **matplotlib/seaborn**: Data visualization
- **tensorflow/pytorch**: Deep learning models

---

## Performance & Scalability

### Current Performance
- **API Calls**: ~26 requests (one per pressure point)
- **Data Points Collected**: ~990 rows
- **Total Runtime**: 3–5 minutes
- **Memory Usage**: <100 MB

### Potential Optimizations
1. **Parallel Requests**: Use `asyncio` or `concurrent.futures` (requires rate limit adjustment)
2. **Caching**: Store NIST responses locally to avoid redundant calls
3. **Extended Range**: Add CO₂ content as a parameter for gas mixtures
4. **Interpolation**: Implement smooth interpolation between pressure points

---

## References

### NIST Chemistry WebBook
- **URL**: https://webbook.nist.gov/chemistry/
- **Fluid Properties**: https://webbook.nist.gov/chemistry/fluid/

### Viscosity Information
- **Reference State**: Ideal gas reference state (default in NIST outputs)
- **Units**: Default output is microPa·s (micropoise)
- **Accuracy**: Typically ±3–5% for experimental correlations

### Related Standards
- **NIST Standard Reference Database 69**: NIST Chemistry WebBook
- **ISO 3448**: Industrial liquid lubricants — ISO viscosity grading
- **ASTM D341**: Viscosity-Temperature Charts

---

## Contributing

Contributions are welcome! Potential areas for improvement:

1. Support for additional gases (CO₂, H₂S, hydrocarbon mixtures)
2. Enhanced error handling and retry logic
3. Parallel/async data fetching
4. Integration with other thermodynamic databases
5. Unit conversion utilities

---

## License

This project is provided as-is for academic and research purposes.

---

## Citation

If you use this data extractor in academic work, please reference:

```bibtex
@misc{nist-viscosity-extractor,
  author = {Akpan, Prince Clarence},
  title = {NIST Gas Viscosity Data Extractor for HPHT Conditions},
  year = {2024},
  institution = {University of Port Harcourt, Department of Gas Engineering},
  url = {https://github.com/Numba1ne/nist-gas-viscosity-extractor}
}
```

---

## Contact & Support

**Author**: Prince Clarence Akpan  
**Email**: Contact via GitHub profile  
**Institution**: University of Port Harcourt, Department of Gas Engineering  

For issues with NIST data access, visit their official support page at https://webbook.nist.gov/

---

## Changelog

### Version 1.0 (Initial Release)
- ✓ Core extraction functionality for methane and nitrogen
- ✓ 26 pressure points, 21 temperature points
- ✓ Dual output formats (model-ready and full detail)
- ✓ Data validation and unit conversion
- ✓ Polite request scheduling (1-second delays)

---

## Disclaimer

This tool automatically retrieves data from the NIST Chemistry WebBook. While the source is authoritative and peer-reviewed, users are responsible for:

1. **Verifying data accuracy** for critical applications
2. **Respecting NIST's terms of service** regarding data usage
3. **Proper attribution** to NIST when using this data
4. **Checking for updates** to NIST databases periodically

The University of Port Harcourt and the author assume no liability for misuse or misapplication of this data.

---

**Last Updated**: May 27, 2024  
**Status**: Active & Maintained
