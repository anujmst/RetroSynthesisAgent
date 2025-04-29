#!/usr/bin/env python3
"""
Module to convert chemical names to SMILES strings using CAS Common Chemistry API
with a fallback to PubChem.
"""
import re
import urllib.parse
import requests
from typing import Tuple

class NameToSMILES:
    """
    Convert a compound, molecule, or reaction name to its SMILES representation
    using the CAS Common Chemistry API with a fallback to PubChem.
    """

    @staticmethod
    def convert(query: str) -> Tuple[bool, str]:
        """
        Convert a chemical name to SMILES string.

        Args:
            query: Chemical name to convert

        Returns:
            Tuple of (success, result)
            - If successful, (True, SMILES string)
            - If failed, (False, error message)
        """
        try:
            if re.search(r"[=#@\\/[\]]", query) or len(query) > 100:
                return False, f"Error: This looks like a SMILES string, not a name."

            # First try CAS Common Chemistry
            success, cas_result = NameToSMILES._try_cas_common_chemistry(query)

            # If CAS has SMILES, return it
            if success:
                print(f"Found SMILES for '{query}' from CAS Common Chemistry: {cas_result}")
                return True, cas_result

            # Otherwise try PubChem as fallback
            success, pubchem_result = NameToSMILES._try_pubchem(query)
            if success:
                print(f"Found SMILES for '{query}' from PubChem: {pubchem_result}")
                return True, pubchem_result

            # If both fail, return error message
            return False, f"No SMILES found for '{query}'"

        except Exception as e:
            return False, f"Exception occurred: {str(e)}"

    @staticmethod
    def _try_cas_common_chemistry(query: str) -> Tuple[bool, str]:
        """
        Try to get SMILES from CAS Common Chemistry.

        Returns:
            Tuple of (success, result)
        """
        try:
            # Step 1: Search by name
            search_url = f"https://commonchemistry.cas.org/api/search?q={query}"
            search_resp = requests.get(search_url)
            search_resp.raise_for_status()

            results = search_resp.json()

            if not results or "results" not in results or not results["results"]:
                return False, f"No results found for '{query}' in CAS Common Chemistry."

            cas_rn = results["results"][0].get("rn")
            if not cas_rn:
                return False, f"CAS RN not found for '{query}'"

            # Step 2: Get SMILES from detail endpoint
            detail_url = f"https://commonchemistry.cas.org/api/detail?cas_rn={cas_rn}"
            detail_resp = requests.get(detail_url)
            detail_resp.raise_for_status()

            details = detail_resp.json()

            # Check for smile and canonicalSmile (singular, not plural)
            smiles = None
            if "smile" in details and details["smile"]:
                smiles = details["smile"]
            elif "canonicalSmile" in details and details["canonicalSmile"]:
                smiles = details["canonicalSmile"]

            if smiles:
                return True, smiles
            else:
                return False, f"No SMILES available in CAS Common Chemistry."

        except Exception as e:
            return False, f"CAS Common Chemistry error: {str(e)}"

    @staticmethod
    def _try_pubchem(query: str) -> Tuple[bool, str]:
        """
        Try to get SMILES from PubChem.

        Returns:
            Tuple of (success, result)
        """
        try:
            # URL encode the query for safety
            encoded_query = urllib.parse.quote(query)

            # First try the simpler direct property endpoint
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_query}/property/IsomericSMILES,CanonicalSMILES/JSON"
            response = requests.get(url)

            # If that fails, try the search -> property approach
            if response.status_code != 200:
                # Search for the compound to get CID
                search_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_query}/cids/JSON"
                search_resp = requests.get(search_url)
                search_resp.raise_for_status()

                search_data = search_resp.json()

                if "IdentifierList" not in search_data or "CID" not in search_data["IdentifierList"]:
                    return False, f"No results found for '{query}' in PubChem."

                cid = search_data["IdentifierList"]["CID"][0]

                # Get compound properties including SMILES
                prop_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IsomericSMILES,CanonicalSMILES/JSON"
                response = requests.get(prop_url)
                response.raise_for_status()

            prop_data = response.json()

            if "PropertyTable" not in prop_data or "Properties" not in prop_data["PropertyTable"] or not prop_data["PropertyTable"]["Properties"]:
                return False, f"Properties not found for '{query}' in PubChem."

            properties = prop_data["PropertyTable"]["Properties"][0]

            # Prefer IsomericSMILES if available, otherwise use CanonicalSMILES
            smiles = properties.get("IsomericSMILES", properties.get("CanonicalSMILES"))

            if smiles:
                return True, smiles
            else:
                return False, f"No SMILES available in PubChem."

        except Exception as e:
            return False, f"PubChem error: {str(e)}"


def main():
    """
    Simple test function for the NameToSMILES class.
    """
    test_compounds = [
        "aspirin",
        "benzanilide",
        "paracetamol",
        "ibuprofen",
        "caffeine"
    ]

    for compound in test_compounds:
        print(f"Converting '{compound}' to SMILES...")
        success, result = NameToSMILES.convert(compound)
        if success:
            print(f"Success: {result}")
        else:
            print(f"Failed: {result}")
        print()


if __name__ == "__main__":
    main()
