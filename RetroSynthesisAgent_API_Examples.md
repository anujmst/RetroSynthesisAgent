# RetroSynthesisAgent: API Usage Examples

## API Endpoints

The RetroSynthesisAgent provides a RESTful API built with FastAPI. The main endpoints are:

### 1. Retrosynthesis Analysis

**Endpoint:** `/retro-synthesis/`  
**Method:** POST  
**Description:** Performs retrosynthetic analysis for a given material

#### Request Parameters

| Parameter  | Type    | Required | Default | Description                                      |
|------------|---------|----------|---------|--------------------------------------------------|
| material   | string  | Yes      | -       | Target material name (e.g., "polyimide")         |
| num_results| integer | Yes      | -       | Number of PDF results to download and process    |
| alignment  | boolean | No       | false   | Whether to perform entity alignment              |
| expansion  | boolean | No       | false   | Whether to expand the tree with additional literature |
| filtration | boolean | No       | false   | Whether to filter reactions/pathways             |

#### Response Format

```json
{
    "status": "success",
    "data": {
        "recommended_pathway": [
            "idx1",
            "idx3",
            "idx5"
        ],
        "reactions": [
            {
                "idx": "idx1",
                "reactants": [
                    "4-chloro-3-nitrobenzoic acid",
                    "2",
                    "6-difluorobenzamide"
                ],
                "products": [
                    "4-chloro-3-nitro-N-(2",
                    "6-difluorobenzoyl)benzamide"
                ],
                "smiles": "O=C(NC(=O)c1c(F)cccc1F)c1cc(Cl)c(cc1)[N+](=O)[O-]",
                "conditions": {
                    "solvent": "DMF",
                    "temperature": "80°C",
                    "catalyst": "EDCI",
                    "reaction time": "12 hours"
                },
                "source": "Journal of Organic Chemistry",
                "source_link": "Link"
            },
            {
                "idx": "idx3",
                "reactants": [
                    "4-chloro-3-nitro-N-(2",
                    "6-difluorobenzoyl)benzamide",
                    "hydrazine hydrate"
                ],
                "products": [
                    "4-chloro-3-amino-N-(2",
                    "6-difluorobenzoyl)benzamide"
                ],
                "smiles": "O=C(NC(=O)c1c(F)cccc1F)c1cc(Cl)c(cc1)N",
                "conditions": {
                    "solvent": "Ethanol",
                    "temperature": "Reflux",
                    "reaction time": "6 hours"
                },
                "source": "Journal of Organic Chemistry",
                "source_link": "Link"
            },
            {
                "idx": "idx5",
                "reactants": [
                    "4-chloro-3-amino-N-(2",
                    "6-difluorobenzoyl)benzamide",
                    "phosgene"
                ],
                "products": [
                    "Flubendiamide"
                ],
                "smiles": "O=C(NC(=O)c1c(F)cccc1F)c1cc(Cl)c(cc1)NC(=O)Cl",
                "conditions": {
                    "solvent": "Toluene",
                    "temperature": "60°C",
                    "reaction time": "4 hours"
                },
                "source": "Journal of Organic Chemistry",
                "source_link": "Link"
            }
        ],
        "reasons": "This pathway was selected due to its high yield and efficiency in producing flubendiamide. The use of readily available starting materials and common reagents makes it economically viable. Additionally, the conditions are mild and scalable, which is advantageous for commercial production. The pathway also minimizes the formation of by-products, ensuring a high purity of the final product. Other pathways were less favorable due to either lower yields, more complex reaction conditions, or the use of hazardous reagents."
    }
}
```

### 2. Health Check

**Endpoint:** `/`  
**Method:** GET  
**Description:** Simple health check to verify the API is running

#### Response Format

```json
{
  "message": "RetroSynthesisAgent API is running."
}
```

## Sample API Requests

### Using cURL

#### Basic Retrosynthesis Request

```bash
curl --location 'http://localhost:8000/retro-synthesis/' \
--header 'Content-Type: application/json' \
--data '{
  "material": "polyimide",
  "num_results": 10,
  "alignment": true,
  "expansion": false,
  "filtration": false
}'
```

#### Complete Retrosynthesis Request

```bash
curl --location 'http://localhost:8000/retro-synthesis/' \
--header 'Content-Type: application/json' \
--data '{
  "material": "polyimide",
  "num_results": 15,
  "alignment": true,
  "expansion": true,
  "filtration": true
}'
```

#### Health Check

```bash
curl --location 'http://localhost:8000/'
```

### Using Python Requests

```python
import requests
import json

# API endpoint
url = "http://localhost:8000/retro-synthesis/"

# Request payload
payload = {
    "material": "polyimide",
    "num_results": 15,
    "alignment": True,
    "expansion": True,
    "filtration": True
}

# Send POST request
response = requests.post(url, json=payload)

# Parse response
if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Node count: {result['data']['node_count']}")
    print(f"Pathway count: {result['data']['pathway_count']}")
    
    # Print recommended pathway
    recommended = result['data']['recommended_pathway']
    print(f"Recommended pathway: {recommended['path_id']}")
    print(f"Reason: {recommended['reason']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

### Using JavaScript Fetch

```javascript
// API endpoint
const url = 'http://localhost:8000/retro-synthesis/';

// Request payload
const payload = {
  material: 'polyimide',
  num_results: 15,
  alignment: true,
  expansion: true,
  filtration: true
};

// Send POST request
fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => {
  console.log('Status:', data.status);
  console.log('Node count:', data.data.node_count);
  console.log('Pathway count:', data.data.pathway_count);
  
  // Print recommended pathway
  const recommended = data.data.recommended_pathway;
  console.log('Recommended pathway:', recommended.path_id);
  console.log('Reason:', recommended.reason);
})
.catch(error => {
  console.error('Error:', error);
});
```

## Visualization API

The RetroSynthesisAgent also provides a separate API for visualization, which can be accessed through a web browser.

### Endpoints

#### 1. Main Visualization Page

**Endpoint:** `/`  
**Method:** GET  
**Description:** Displays the main visualization page

#### 2. Tree Data

**Endpoint:** `/api/double`  
**Method:** GET  
**Description:** Returns data for two trees (main tree and unexpanded tree)

**Response Format:**
```json
{
  "bigTree": {
    "name": "target_material",
    "children": [
      // Tree structure...
    ]
  },
  "smallTree": {
    "name": "target_material",
    "children": [
      // Tree structure...
    ]
  }
}
```

#### 3. Multiple Tree Comparison

**Endpoint:** `/api/three`  
**Method:** GET  
**Description:** Returns data for three trees (main, unexpanded, and pathway 1)

**Endpoint:** `/api/quad`  
**Method:** GET  
**Description:** Returns data for four trees (main, unexpanded, pathway 1, and pathway 2)

## Integration Examples

### Integrating with a Web Application

```javascript
// Example of integrating the RetroSynthesisAgent API with a web application

document.getElementById('synthesis-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const material = document.getElementById('material-input').value;
  const numResults = parseInt(document.getElementById('num-results-input').value);
  const alignment = document.getElementById('alignment-checkbox').checked;
  const expansion = document.getElementById('expansion-checkbox').checked;
  const filtration = document.getElementById('filtration-checkbox').checked;
  
  // Show loading indicator
  document.getElementById('loading-indicator').style.display = 'block';
  document.getElementById('results-container').style.display = 'none';
  
  try {
    const response = await fetch('http://localhost:8000/retro-synthesis/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        material,
        num_results: numResults,
        alignment,
        expansion,
        filtration
      })
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      // Display results
      document.getElementById('node-count').textContent = data.data.node_count;
      document.getElementById('pathway-count').textContent = data.data.pathway_count;
      
      // Display recommended pathway
      const recommended = data.data.recommended_pathway;
      document.getElementById('recommended-pathway').textContent = recommended.path_id;
      document.getElementById('recommendation-reason').textContent = recommended.reason;
      
      // Show visualization link
      document.getElementById('visualization-link').href = 'http://localhost:8000/';
      document.getElementById('visualization-link').style.display = 'block';
      
      // Show results container
      document.getElementById('results-container').style.display = 'block';
    } else {
      alert('Error: ' + data.message);
    }
  } catch (error) {
    alert('Error: ' + error.message);
  } finally {
    // Hide loading indicator
    document.getElementById('loading-indicator').style.display = 'none';
  }
});
```

### Integrating with a Python Script

```python
import requests
import json
import time
import webbrowser

def run_retrosynthesis(material, num_results=10, alignment=True, expansion=True, filtration=True):
    """
    Run retrosynthetic analysis for a given material and open the visualization.
    
    Parameters:
    material (str): Target material name
    num_results (int): Number of PDF results to download and process
    alignment (bool): Whether to perform entity alignment
    expansion (bool): Whether to expand the tree with additional literature
    filtration (bool): Whether to filter reactions/pathways
    
    Returns:
    dict: Analysis results
    """
    # API endpoint
    url = "http://localhost:8000/retro-synthesis/"
    
    # Request payload
    payload = {
        "material": material,
        "num_results": num_results,
        "alignment": alignment,
        "expansion": expansion,
        "filtration": filtration
    }
    
    print(f"Starting retrosynthetic analysis for {material}...")
    print(f"Parameters: num_results={num_results}, alignment={alignment}, expansion={expansion}, filtration={filtration}")
    
    # Send POST request
    response = requests.post(url, json=payload)
    
    # Parse response
    if response.status_code == 200:
        result = response.json()
        print(f"Analysis completed successfully!")
        print(f"Node count: {result['data']['node_count']}")
        print(f"Pathway count: {result['data']['pathway_count']}")
        
        # Print recommended pathway
        recommended = result['data']['recommended_pathway']
        print(f"Recommended pathway: {recommended['path_id']}")
        print(f"Reason: {recommended['reason']}")
        
        # Open visualization in browser
        print("Opening visualization in browser...")
        webbrowser.open("http://localhost:8000/")
        
        return result['data']
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # Example usage
    material = input("Enter target material: ")
    num_results = int(input("Enter number of papers to download (default: 10): ") or "10")
    
    print("Starting analysis...")
    results = run_retrosynthesis(material, num_results)
    
    # Save results to file
    if results:
        filename = f"{material}_results.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")
```
