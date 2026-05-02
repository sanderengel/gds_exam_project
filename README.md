# Lightning Strikes and Wildfare during the 2020 California Lightning Siege

This app allows you to explore ...

## Getting Started

### 1. Prerequisites

Install [Pixi](https://pixi.prefix.dev/latest/) by running:

**macOS / Linux:**
```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

**Windows:**
```PowerShell
iwr -useb https://pixi.sh/install.ps1 | iex
```

Note: You might have to restart your terminal after installation for the pixi command to become available._

### 2. Clone the Repository

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/sanderengel/gds_exam_project

cd gds_exam_project
```

### 3. Environment Setup

This project uses [Pixi](https://pixi.prefix.dev/latest/) for environment management and dependency tracking. The environment is defined via the `pixi.toml` and `pixi.lock` files. 

To create the environment and install all necessary dependencies (including Python, spatial libraries, and command-line tools like `curl`), run:

```bash
pixi install
```

## App

Use the app by running:

```bash
pixi run app
```

## Raw Data

We collect the raw lightning and fire data through NASA Earthdata and NASA FIRMS, respectively. 

The raw fire data can be found at `data/fire/DL_FIRE_SV-C2_730956/fire_archive_SV-C2_730956.csv`.

Due to the large size of the raw lightning data, we cannot upload here to this repo. Instead, here is a (barely) short guide of how to fetch the data.

### NASA Earthdata GLMCIERRA Lightning Strikes

1. **Account & Authorization:** Create a free account at [NASA Earthdata](https://urs.earthdata.nasa.gov/profile). You will likely be asked to authorize, which you must do. 

2. **Run Download Script:** Navigate to the root directory of this repository and run the command below. Please note that the dataset consists of approximately 1,800 files. The total size is around 8GB, and the download will likely take several minutes depending on your connection.

   ```bash
   pixi run download-lightning
   ```

3. **Authentication:** Once the script starts, it will ask you for the Earthdata username and password. The script handles the transfer and temporarily stores your credentials in a secure `.netrc` file to authenticate each granule. 

4. **Store:** The files will be automatically saved to `data/lightning/glmcierra/`. Ensure you have enough disk space before begining the process.

## Processed Lightning and Fire Data

Due to the nature of NASA satellite granules, the raw lightning data contains many lightning strike observations outside the California boundary. We remove these and clean and enhance the data (e.g. by adding `h3` hexagonal tessellation IDs) in `process_data/process_lightning.py`. The raw fire data is better contained, but we nonetheless clean it, enhance it, and aggregate to polygons in `process_data/process_fire.py`. For both, the processed data is stored in `.feather` files and available directly in the repo at:

- `data/lightning/california_lightning_siege_2020.feather`
- `data/fire/california_fire_polygons.feather`

If you went through the trouble of downloading the raw data as described above, you might want to re-process it yourself. To process the raw data and generate the two `.feather` files mentioned above, run the following command:

```bash
pixi run process-data
```

The above command will process both raw lightning and fire data. To process only one of the two, run the corresponding command:

```bash
python process_data/process_lightning.py

python process_data/process_fire.py
```

## Re-Compute the Risk Layer

The risk layer data is available inside the repo, but you might want to re-compute it yourself. You can do so be following the steps below:

1. **Compute Engineered Features:** To compute the risk layer, we compute a small range of features on a `h3` grid over relevant cells in California. We once again meet the issue of a file being too large to comfortably fit inside this Repo. While the risk layer itself is available, the underlying features required to build it isn't. You can re-engineer these by running the below command, after which the features file will then be stored in `data/features/feature_grid.feather`. 

```bash
pixi run build-grid
```

2. **Compute Risk Layer:** Rebuild the risk layer by running:

```bash
pixi run build-risk
```

## Authors

Sander Engel Thilo

_<saet@itu.dk>_

**IT University of Copenhagen**