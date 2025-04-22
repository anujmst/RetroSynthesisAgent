# RetroSynthesisAgent: Installation and Setup Guide

This guide provides detailed instructions for installing and setting up the RetroSynthesisAgent system on your local machine.

## System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.11 or higher
- **RAM**: Minimum 8GB, recommended 16GB+
- **Storage**: At least 10GB of free space (for downloaded PDFs and data)
- **Internet Connection**: Required for downloading papers and accessing the OpenAI API

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/RetroSynthesisAgent.git
cd RetroSynthesisAgent
```

### 2. Set Up Python Environment

#### Using Conda (Recommended)

```bash
# Create a new conda environment
conda create -n retrosyn python=3.11
conda activate retrosyn

# Install required packages
pip install rdkit requests python-dotenv PyMuPDF scholarly openai networkx graphviz pubchempy Pillow fastapi pydantic uvicorn pyvis loguru
```

#### Using venv

```bash
# Create a new virtual environment
python -m venv retrosyn_env
source retrosyn_env/bin/activate  # On Windows: retrosyn_env\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 3. Download and Process eMolecules Data

The RetroSynthesisAgent uses the eMolecules dataset to identify commercially available chemical compounds. Follow these steps to set up the dataset:

1. Download the eMolecules dataset from: https://downloads.emolecules.com/free/
   - For this project, version 2024-07-01 is recommended
   - The file will be named something like `version-2024-07-01.smi.gz`

2. Place the downloaded file in the project root directory and rename it to `version.smi.gz`

3. Process the dataset:
   ```bash
   python create.py
   ```

   This script will:
   - Extract SMILES strings from the gzipped file
   - Remove duplicates
   - Save the processed data as a JSON file in the RetroSynAgent directory

4. Verify that the file `RetroSynAgent/emol.json` has been created

### 4. Configure Environment Variables

Create a `.env` file in the project root directory with the following content:

```
API_KEY=your_openai_api_key
BASE_URL=optional_openai_api_base_url
HEADERS={"user-agent": "your_user_agent"}
COOKIES={"cookie1": "value1", "cookie2": "value2"}
```

#### Obtaining OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in to your account
3. Navigate to the API keys section
4. Create a new API key
5. Copy the key and paste it into your `.env` file

#### Obtaining Headers and Cookies for Web Scraping

The system needs headers and cookies to download scientific papers. Here's how to obtain them:

1. Open your web browser (Chrome or Firefox recommended)
2. Open the developer tools (F12 or right-click and select "Inspect")
3. Go to the "Network" tab
4. Visit a scientific paper repository website (e.g., sci-hub.se)
5. Look for any request in the Network tab
6. Right-click on the request and select "Copy as cURL"
7. Extract the headers and cookies from the cURL command
8. Format them as JSON and add them to your `.env` file

Example:
```
HEADERS={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
COOKIES={"__cfduid": "d1234567890abcdef1234567890abcdef1234", "session": "1234567890abcdef1234567890abcdef"}
```

### 5. Create Required Directories

The system requires several directories to store downloaded PDFs, results, and trees. Run the following commands to create them:

```bash
mkdir -p pdf_pi
mkdir -p res_pi
mkdir -p tree_pi
```

### 6. Verify Installation

To verify that everything is set up correctly, run a simple test:

```bash
python main.py --material aspirin --num_results 2 --alignment False --expansion False --filtration False
```

This should:
1. Download 2 papers related to aspirin synthesis
2. Process the papers to extract reactions
3. Build a simple retrosynthetic tree
4. Save the results in the appropriate directories

## Running the System

### Command Line Interface

To run the RetroSynthesisAgent from the command line:

```bash
python main.py --material [MATERIAL_NAME] --num_results [NUMBER_OF_PAPERS] --alignment [True/False] --expansion [True/False] --filtration [True/False]
```

Example:
```bash
python main.py --material polyimide --num_results 15 --alignment True --expansion True --filtration True
```

### API Server

To start the API server:

```bash
uvicorn api:app --reload
```

This will start the server at http://localhost:8000

You can then make API requests as described in the API documentation.

### Visualization Server

To start the visualization server:

```bash
uvicorn vistree:app --reload
```

This will start the visualization server at http://localhost:8000

Open your web browser and navigate to http://localhost:8000 to view the interactive visualization.

## Troubleshooting

### Common Installation Issues

#### 1. RDKit Installation Fails

RDKit can be challenging to install with pip. If you encounter issues, try installing it with conda:

```bash
conda install -c conda-forge rdkit
```

#### 2. PyMuPDF Installation Issues

If you encounter issues with PyMuPDF, try installing it separately:

```bash
pip install --upgrade pip
pip install PyMuPDF==1.25.1
```

#### 3. Graphviz Dependency

The graphviz Python package requires the Graphviz software to be installed on your system:

- **Windows**: Download and install from https://graphviz.org/download/
- **macOS**: `brew install graphviz`
- **Linux**: `apt-get install graphviz` or `yum install graphviz`

#### 4. Environment Variable Issues

If the system cannot find your API key or other environment variables, make sure:
- The `.env` file is in the correct location (project root)
- The variable names match exactly (API_KEY, BASE_URL, HEADERS, COOKIES)
- There are no spaces around the equals sign (use `API_KEY=value`, not `API_KEY = value`)

### Runtime Issues

#### 1. PDF Download Failures

If the system fails to download PDFs:
- Check your internet connection
- Verify that the HEADERS and COOKIES in your `.env` file are up to date
- Try using a VPN if you're experiencing regional restrictions
- Some papers may not be available for download

#### 2. OpenAI API Errors

If you encounter errors with the OpenAI API:
- Verify that your API key is correct
- Check your API usage limits and billing status
- Consider using a different model if you're experiencing rate limits
- If using a custom BASE_URL, ensure it's correctly formatted

#### 3. Memory Issues

If the system runs out of memory:
- Reduce the number of papers to download
- Close other memory-intensive applications
- Consider upgrading your RAM
- Process papers in smaller batches

## Updating the System

To update the RetroSynthesisAgent to the latest version:

```bash
git pull origin main
pip install -r requirements.txt
```

## Uninstallation

To uninstall the RetroSynthesisAgent:

1. Remove the project directory:
   ```bash
   rm -rf RetroSynthesisAgent
   ```

2. Remove the conda environment (if used):
   ```bash
   conda deactivate
   conda env remove -n retrosyn
   ```

3. Remove the virtual environment (if used):
   ```bash
   rm -rf retrosyn_env
   ```
