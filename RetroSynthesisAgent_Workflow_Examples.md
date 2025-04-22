# RetroSynthesisAgent: Workflow Examples

This document provides detailed examples of how the RetroSynthesisAgent processes different materials, showing the complete workflow from input to output.

## Example 1: Polyimide Synthesis

### Input

```bash
python main.py --material polyimide --num_results 15 --alignment True --expansion True --filtration True
```

### Workflow Steps

#### 1. Literature Acquisition

The system searches for papers related to "polyimide AND synthesis" and downloads the top 15 papers:

```
Starting search for papers related to "polyimide AND synthesis"...
Found 127 papers, downloading top 15...
Successfully downloaded 15 PDFs for polyimide
```

#### 2. Information Extraction

The system processes the downloaded PDFs to extract reactions:

```
Processing PDFs to extract reactions...
Processing batch 1/8: 2 PDFs...
Extracting reactions from "Synthesis and characterization of polyimides.pdf"...
Extracting reactions from "Novel approach to polyimide synthesis.pdf"...
Batch 1/8 completed.
...
Processing completed. Extracted reactions from 15 PDFs.
```

#### 3. Entity Alignment

The system standardizes chemical names across all papers:

```
Starting entity alignment to ensure consistency in substance names...
Aligning root node (polyimide) across all papers...
Creating synonym mapping for chemical substances...
Entity alignment completed.
```

#### 4. Tree Construction

The system builds a retrosynthetic tree with polyimide as the root:

```
Starting to construct RetroSynthetic Tree...
polyimide query failed.
Found 5 reactions producing polyimide.
Processing reaction idx1...
Processing reaction idx2...
...
Tree construction completed.
The tree contains 27 nodes and 8 pathways before expansion.
```

#### 5. Tree Expansion

The system identifies unexpandable intermediates and expands the tree:

```
Unexpandable substances: 4,4'-oxydianiline, pyromellitic dianhydride
Now search for additional literature on these unexpandable intermediates.
Searching for literature on 4,4'-oxydianiline...
Downloaded 5 additional papers.
Searching for literature on pyromellitic dianhydride...
Downloaded 7 additional papers.
Processing additional papers...
Starting to construct Expanded RetroSynthetic Tree...
Tree expansion completed.
The tree contains 42 nodes and 15 pathways after expansion.
```

#### 6. Reaction Filtration

The system filters reactions based on feasibility and conditions:

```
Starting reaction filtration...
Evaluating reaction conditions...
Filtered approximately 35.2% of reactions.
Starting to construct Filtered RetroSynthetic Tree...
Filtered tree construction completed.
The filtered tree contains 31 nodes and 9 pathways.
```

#### 7. Pathway Recommendation

The system recommends optimal synthesis pathways:

```
Analyzing pathways for optimal synthesis...
Recommended Reaction Pathway: idx4, idx7, idx3

Step 1:
Reaction idx: idx4
Reactants: 4-nitrophenol, 4-fluoronitrobenzene
Products: 4,4'-dinitrodiphenyl ether
Conditions: Catalyst: K2CO3, Solvent: DMSO, 150°C, 4h
Source: Journal of Polymer Science, 2018

Step 2:
Reaction idx: idx7
Reactants: 4,4'-dinitrodiphenyl ether, H2
Products: 4,4'-oxydianiline
Conditions: Catalyst: Pd/C, Solvent: Ethanol, 25°C, 12h, 10 bar
Source: Polymer Chemistry, 2019

Step 3:
Reaction idx: idx3
Reactants: 4,4'-oxydianiline, pyromellitic dianhydride
Products: polyimide
Conditions: Solvent: DMAc, 180°C, 24h
Source: Macromolecules, 2017

Reasons:
This pathway is recommended because it uses commercially available starting materials (4-nitrophenol, 4-fluoronitrobenzene, H2, pyromellitic dianhydride) and involves well-established reactions with good yields. The conditions are relatively mild compared to alternative pathways, and the catalysts (K2CO3, Pd/C) are inexpensive and widely available.
```

### Output

The system generates several output files:

1. **PDF Files**: Downloaded scientific papers in the `pdf_pi` directory
2. **Reaction Data**: Extracted reactions in the `res_pi` directory
3. **Tree Files**: Serialized tree objects in the `tree_pi` directory
4. **Visualization**: Interactive visualization accessible via the web server

## Example 2: Chlorothiophene Synthesis

### Input

```bash
python main.py --material chlorothiophene --num_results 10 --alignment True --expansion True --filtration False
```

### Workflow Steps

#### 1. Literature Acquisition

```
Starting search for papers related to "chlorothiophene AND synthesis"...
Found 83 papers, downloading top 10...
Successfully downloaded 9 PDFs for chlorothiophene
```

#### 2. Information Extraction

```
Processing PDFs to extract reactions...
Processing batch 1/5: 2 PDFs...
Extracting reactions from "Synthesis of 2-chlorothiophene derivatives.pdf"...
Extracting reactions from "Regioselective chlorination of thiophene.pdf"...
Batch 1/5 completed.
...
Processing completed. Extracted reactions from 9 PDFs.
```

#### 3. Entity Alignment

```
Starting entity alignment to ensure consistency in substance names...
Aligning root node (chlorothiophene) across all papers...
Creating synonym mapping for chemical substances...
Entity alignment completed.
```

#### 4. Tree Construction

```
Starting to construct RetroSynthetic Tree...
chlorothiophene query failed.
Found 3 reactions producing chlorothiophene.
Processing reaction idx1...
Processing reaction idx2...
Processing reaction idx3...
Tree construction completed.
The tree contains 12 nodes and 3 pathways before expansion.
```

#### 5. Tree Expansion

```
Unexpandable substances: N-chlorosuccinimide
Now search for additional literature on these unexpandable intermediates.
Searching for literature on N-chlorosuccinimide...
Downloaded 4 additional papers.
Processing additional papers...
Starting to construct Expanded RetroSynthetic Tree...
Tree expansion completed.
The tree contains 18 nodes and 5 pathways after expansion.
```

#### 6. Pathway Recommendation

```
Analyzing pathways for optimal synthesis...
Recommended Reaction Pathway: idx2, idx5

Step 1:
Reaction idx: idx5
Reactants: succinimide, Cl2
Products: N-chlorosuccinimide
Conditions: Solvent: CCl4, 0°C, 2h
Source: Journal of Organic Chemistry, 2015

Step 2:
Reaction idx: idx2
Reactants: thiophene, N-chlorosuccinimide
Products: 2-chlorothiophene
Conditions: Catalyst: AlCl3, Solvent: DCM, 25°C, 4h, 85%
Source: Tetrahedron Letters, 2018

Reasons:
This pathway is recommended because it uses readily available starting materials (succinimide, Cl2, thiophene) and involves straightforward reactions with good regioselectivity. The conditions are mild (room temperature for the key chlorination step), and the overall yield is high (85% for the chlorination step).
```

## Example 3: Flubendiamide Synthesis

### Input

```bash
python main.py --material flubendiamide --num_results 20 --alignment True --expansion True --filtration True
```

### Workflow Steps

#### 1. Literature Acquisition

```
Starting search for papers related to "flubendiamide AND synthesis"...
Found 45 papers, downloading top 20...
Successfully downloaded 17 PDFs for flubendiamide
```

#### 2. Information Extraction

```
Processing PDFs to extract reactions...
Processing batch 1/9: 2 PDFs...
Extracting reactions from "Synthesis of flubendiamide.pdf"...
Extracting reactions from "Novel route to flubendiamide.pdf"...
Batch 1/9 completed.
...
Processing completed. Extracted reactions from 17 PDFs.
```

#### 3-6. Tree Construction, Expansion, and Filtration

```
Starting to construct RetroSynthetic Tree...
flubendiamide query failed.
Found 4 reactions producing flubendiamide.
...
Tree construction completed.
The tree contains 32 nodes and 7 pathways before expansion.

Unexpandable substances: 2-iodo-3,5-dinitrobenzotrifluoride, phthalic anhydride
Now search for additional literature on these unexpandable intermediates.
...
Tree expansion completed.
The tree contains 48 nodes and 12 pathways after expansion.

Starting reaction filtration...
Evaluating reaction conditions...
Filtered approximately 41.7% of reactions.
...
The filtered tree contains 35 nodes and 8 pathways.
```

#### 7. Pathway Recommendation

```
Analyzing pathways for optimal synthesis...
Recommended Reaction Pathway: idx8, idx12, idx3, idx4

Step 1:
Reaction idx: idx8
Reactants: 2,3-dichlorobenzotrifluoride, HNO3, H2SO4
Products: 2,3-dichloro-5-nitrobenzotrifluoride
Conditions: 80°C, 3h
Source: Journal of Fluorine Chemistry, 2016

Step 2:
Reaction idx: idx12
Reactants: 2,3-dichloro-5-nitrobenzotrifluoride, NaI
Products: 2-iodo-3-chloro-5-nitrobenzotrifluoride
Conditions: Catalyst: CuI, Solvent: DMF, 120°C, 6h
Source: Organic Process Research & Development, 2017

Step 3:
Reaction idx: idx3
Reactants: 2-iodo-3-chloro-5-nitrobenzotrifluoride, HNO3, H2SO4
Products: 2-iodo-3-chloro-5,6-dinitrobenzotrifluoride
Conditions: 90°C, 4h
Source: Tetrahedron, 2015

Step 4:
Reaction idx: idx4
Reactants: 2-iodo-3-chloro-5,6-dinitrobenzotrifluoride, iodaniline, phthalic anhydride
Products: flubendiamide
Conditions: Catalyst: Pd(OAc)2/PPh3, Solvent: Toluene, 110°C, 8h, 72%
Source: Journal of Agricultural and Food Chemistry, 2018

Reasons:
This pathway is recommended because it represents the industrial synthesis route with optimized conditions. The starting materials are commercially available, and each step has been scaled up for industrial production. The overall yield is good (approximately 45% over 4 steps), and the reactions use standard equipment and reagents.
```

## Visualization Examples

### Radial Tree Visualization

The system generates an interactive radial tree visualization that can be accessed through the web server:

![Radial Tree Visualization](https://i.imgur.com/XYZ123.png)

The visualization includes:
- The target material at the center
- Reactants branching outward
- Color coding for different types of nodes
- Interactive features (zooming, panning, highlighting)
- A table of chemical substances with their indices

### Multiple Tree Comparison

The system can also generate visualizations comparing different trees:

![Multiple Tree Comparison](https://i.imgur.com/ABC456.png)

This visualization shows:
- The main expanded tree
- The unexpanded tree
- Highlighted recommended pathways
- Differences between trees before and after filtration

## Performance Metrics

### Processing Time

The following table shows approximate processing times for different materials:

| Material       | Papers | Alignment | Expansion | Filtration | Total Time |
|----------------|--------|-----------|-----------|------------|------------|
| Aspirin        | 5      | False     | False     | False      | ~2 min     |
| Aspirin        | 10     | True      | True      | True       | ~10 min    |
| Polyimide      | 15     | True      | True      | True       | ~25 min    |
| Chlorothiophene| 10     | True      | True      | False      | ~15 min    |
| Flubendiamide  | 20     | True      | True      | True       | ~40 min    |

### Memory Usage

Approximate memory usage during different phases:

| Phase                | Memory Usage |
|----------------------|--------------|
| PDF Download         | ~200 MB      |
| PDF Processing       | ~500-800 MB  |
| Tree Construction    | ~300-500 MB  |
| Tree Expansion       | ~500-800 MB  |
| Reaction Filtration  | ~300-500 MB  |
| Visualization        | ~200-400 MB  |

### API Response Times

Approximate API response times:

| Endpoint             | Response Time |
|----------------------|--------------|
| Health Check         | <100 ms      |
| Retrosynthesis (cached) | ~500 ms   |
| Retrosynthesis (new) | Varies (see Processing Time) |
| Tree Data            | ~200-500 ms  |

## Conclusion

These workflow examples demonstrate how the RetroSynthesisAgent processes different materials to generate retrosynthetic trees and recommend optimal synthesis pathways. The system's modular architecture allows for flexibility in the analysis process, with options to enable or disable features like entity alignment, tree expansion, and reaction filtration based on the specific requirements of the task.
