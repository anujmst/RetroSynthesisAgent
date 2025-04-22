import re
import json

def parse_reaction_data(raw_text: str) -> dict:
    # 1. Extract recommended pathway
    rec_match = re.search(r"Recommended Reaction Pathway:\s*([^\n]+)", raw_text)
    recommended = [idx.strip() for idx in rec_match.group(1).split(",")] if rec_match else []

    # 2. Extract the Reasons block (everything after "Reasons:")
    reasons = ""
    reasons_match = re.search(r"Reasons:\s*((?:.|\n)*)", raw_text)
    if reasons_match:
        reasons = reasons_match.group(1).strip()

    # 3. Split into individual reaction blocks
    blocks = re.split(r"(?=Reaction idx:)", raw_text)
    reactions = []
    for blk in blocks:
        if not blk.strip().startswith("Reaction idx:"):
            continue

        idx_match    = re.search(r"Reaction idx:\s*(\S+)", blk)
        react_match  = re.search(r"Reactants:\s*(.+)", blk)
        prod_match   = re.search(r"Products:\s*(.+)", blk)
        smile_match  = re.search(r"Reaction SMILES:\s*(\S+)", blk)
        cond_match   = re.search(r"Conditions:\s*(.+)", blk)
        source_match = re.search(r"Source:\s*(.+)", blk)
        link_match   = re.search(r"SourceLink:\s*\[?(.+?)\]?(?:\s|$)", blk)

        reaction = {
            "idx":        idx_match.group(1) if idx_match else None,
            "reactants":  [r.strip() for r in react_match.group(1).split(",")] if react_match else [],
            "products":   [p.strip() for p in prod_match.group(1).split(",")]  if prod_match else [],
            "smiles":     smile_match.group(1) if smile_match else None,
            "conditions": {},
            "source":     source_match.group(1).strip() if source_match else None,
            "source_link": link_match.group(1).strip() if link_match else None
        }

        # parse conditions into key/value pairs
        if cond_match:
            for part in cond_match.group(1).split(","):
                if ":" in part:
                    key, val = part.split(":", 1)
                    reaction["conditions"][key.strip().lower()] = val.strip()

        reactions.append(reaction)

    return {
        "recommended_pathway": recommended,
        "reactions": reactions,
        "reasons": reasons
    }


# Example usage:
if __name__ == "__main__":
    raw = """============================================================
Recommended Reaction Pathway: idx1, idx3, idx5

Reaction idx: idx1
Reactants: 4-chloro-3-nitrobenzoic acid, 2,6-difluorobenzamide
Products: 4-chloro-3-nitro-N-(2,6-difluorophenyl)benzamide
Reaction SMILES: O=C(Nc1c(F)cccc1F)c1cc(Cl)c(cc1)[N+](=O)[O-]
Conditions: Solvent: DMF, Temperature: 80°C, Catalyst: EDCI
Source: Journal of Organic Chemistry
SourceLink: [Link to PDF]

Reaction idx: idx3
Reactants: 4-chloro-3-nitro-N-(2,6-difluorophenyl)benzamide, hydrogen gas
Products: 4-chloro-3-amino-N-(2,6-difluorophenyl)benzamide
Reaction SMILES: O=C(Nc1c(F)cccc1F)c1cc(Cl)c(cc1)N
Conditions: Solvent: Ethanol, Catalyst: Pd/C, Pressure: 1 atm
Source: Journal of Organic Chemistry
SourceLink: [Link to PDF]

Reaction idx: idx5
Reactants: 4-chloro-3-amino-N-(2,6-difluorophenyl)benzamide, phosgene
Products: Flubendiamide
Reaction SMILES: O=C(Nc1c(F)cccc1F)c1cc(Cl)c(cc1)NC(=O)Cl
Conditions: Solvent: Toluene, Temperature: 60°C
Source: Journal of Organic Chemistry
SourceLink: [Link to PDF]

Reasons:
This pathway is selected due to its high yield and efficiency in producing flubendiamide. The use of readily available starting materials and common reagents makes it cost-effective. Additionally, the conditions are mild, reducing the risk of side reactions and degradation of the product. The literature sources provide detailed experimental procedures, ensuring reproducibility and reliability of the synthesis. Other pathways were less favorable due to lower yields, more complex reaction conditions, or the use of hazardous reagents.
"""

    structured = parse_reaction_data(raw)
    print(json.dumps(structured, indent=2))
