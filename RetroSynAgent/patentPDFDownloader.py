#!/usr/bin/env python3
"""
Module to search for patents related to a SMILE string, download the PDFs,
and prepare them for processing by RetroSynAgent.
"""
import json
import sys
import re
import requests
import os
from typing import List, Optional, Dict, Tuple
from redis import Redis
from rdkit import Chem
from dotenv import load_dotenv
import time
import urllib3
from tqdm import tqdm

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables from .env file
load_dotenv()

# Compile regex patterns for supported jurisdictions
PATENT_PATTERNS = {
    # US patterns for both grant numbers (7-8 digits) and application numbers (11 digits)
    'US': re.compile(r'^US(\d{7}|\d{8}|\d{11})(?:A1|B1|A2)?$'),  # e.g., US1234567, US20210353574, US20020052003
    'US_APP': re.compile(r'^US\d{4}\d{6}(?:A1|A2)?$'),     # e.g., US20210353574A1
    'EP': re.compile(r'^EP\d{2}\d{6}(?:A1|B1)?$'),         # e.g., EP09787810A, EP2320951B1
    'CN': re.compile(r'^CN\d{8}(?:A|B)?$'),                 # e.g., CN12345678A
    'KR': re.compile(r'^KR\d{10}(?:A1)?$'),                 # e.g., KR1023456789A1
    'JP': re.compile(r'^JP\d{11}(?:A)?$'),                  # e.g., JP2001234567A
}


class PatentPDFDownloader:
    """
    Class to search for patents related to a SMILE string and download the PDFs.
    """
    def __init__(self, pdf_folder_name: str = "patent_pdfs", max_patents: int = 10):
        """
        Initialize the PatentPDFDownloader.

        Args:
            pdf_folder_name: Folder to save downloaded PDFs
            max_patents: Maximum number of patents to download
        """
        self.pdf_folder_name = pdf_folder_name
        self.max_patents = max_patents

        # Create the PDF folder if it doesn't exist
        os.makedirs(pdf_folder_name, exist_ok=True)

        # Set up headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def clean_smile(self, smile: str) -> str:
        """
        Remove stereochemistry from SMILE string as it's not present in PatCID
        """
        try:
            mol = Chem.MolFromSmiles(smile)
            if mol is None:
                raise ValueError("Invalid SMILE string")
            Chem.RemoveStereochemistry(mol)
            return Chem.MolToSmiles(mol, isomericSmiles=False)
        except Exception as e:
            raise ValueError(f"Error processing SMILE string: {str(e)}")

    def get_patent_ids_from_redis(self, smile: str, redis_host: str = "localhost",
                                 redis_port: int = 6379, redis_db: int = 0) -> List[str]:
        """
        Retrieve patent IDs from Redis for a given SMILE string.
        """
        try:
            redis_client = Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=False)
            redis_client.ping()
            key = f"smile:{smile}"
            data = redis_client.get(key)
            if not data:
                return []
            ids = json.loads(data.decode('utf-8'))
            return ids if isinstance(ids, list) else []
        except Exception as e:
            print(f"Error connecting to Redis: {str(e)}")
            return []

    def strip_kind_code(self, patent_id: str) -> str:
        """
        Remove kind code (A1, B1, etc.) from patent ID
        """
        # Remove any kind codes (A1, B1, etc.)
        return re.sub(r'([A-Z]\d?)$', '', patent_id)

    def format_patent_for_url(self, patent_id: str) -> str:
        """
        Format patent ID for use in Google Patents URL
        """
        # Remove any spaces
        patent_id = patent_id.strip()
        return patent_id

    def get_patent_pdf_link(self, patent_id: str) -> Optional[str]:
        """
        Retrieve PDF link for a patent by directly scraping Google Patents website
        """
        # Try with the original patent ID first
        pdf_url = self._try_get_patent_pdf(patent_id)
        if pdf_url:
            return pdf_url

        # If no PDF found, try with different kind codes
        base_id = self.strip_kind_code(patent_id)

        # For US patents, try different kind codes
        if base_id.startswith("US"):
            # For application numbers (US20xxxxxx format)
            if len(base_id) >= 10 and base_id[2:6].isdigit() and int(base_id[2:6]) >= 2000:
                # Try A1, A2 for applications
                for kind_code in ["A1", "A2"]:
                    if not patent_id.endswith(kind_code):
                        pdf_url = self._try_get_patent_pdf(f"{base_id}{kind_code}")
                        if pdf_url:
                            return pdf_url
            # For granted patents (US7654321 format)
            elif base_id[2:].isdigit() and len(base_id[2:]) <= 8:
                # Try B1, B2 for granted patents
                for kind_code in ["B1", "B2"]:
                    if not patent_id.endswith(kind_code):
                        pdf_url = self._try_get_patent_pdf(f"{base_id}{kind_code}")
                        if pdf_url:
                            return pdf_url

        # For EP patents
        elif base_id.startswith("EP"):
            # Try different kind codes for EP patents
            for kind_code in ["A1", "A2", "B1", "B2"]:
                if not patent_id.endswith(kind_code):
                    pdf_url = self._try_get_patent_pdf(f"{base_id}{kind_code}")
                    if pdf_url:
                        return pdf_url

        # If all attempts failed, return None
        return None

    def _try_get_patent_pdf(self, patent_id: str) -> Optional[str]:
        """
        Try to get PDF link for a specific patent ID
        """
        # Format the patent ID for the URL
        formatted_id = self.format_patent_for_url(patent_id)

        # Google Patents URL
        url = f"https://patents.google.com/patent/{formatted_id}/en"

        print(f"Fetching patent information from: {url}")

        # Set up retry parameters
        max_retries = 2  # Reduced retries for each attempt since we're trying multiple variants
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Make the request
                response = requests.get(url, headers=self.headers, timeout=10, verify=False)
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses

                # Extract the PDF URL using regex
                html_content = response.text
                pdf_match = re.search(r'<meta\s+name="citation_pdf_url"\s+content="([^"]+)"', html_content)

                if pdf_match:
                    pdf_url = pdf_match.group(1)
                    print(f"Found PDF URL: {pdf_url}")
                    return pdf_url
                else:
                    print(f"No PDF URL found for {patent_id}")
                    return None

            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = retry_count * 2
                    print(f"Timeout for {patent_id}, retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Timeout for {patent_id} after {max_retries} retries")
                    break

            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
                print(f"HTTP error {status_code} for {patent_id}: {str(e)}")

                # If we get a 429 (Too Many Requests) or 5xx error, retry
                if status_code == 429 or (isinstance(status_code, int) and status_code >= 500):
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = retry_count * 3  # Longer wait for rate limiting
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Failed after {max_retries} retries")
                        break
                else:
                    # For 404 and other client errors, the patent might not exist
                    if status_code == 404:
                        print(f"Patent {patent_id} not found (404)")
                    break

            except Exception as e:
                print(f"Error fetching {patent_id}: {str(e)}")
                retry_count += 1
                if retry_count <= max_retries:
                    wait_time = retry_count * 2
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    break

        return None

    def download_pdf(self, pdf_url: str, patent_id: str) -> Optional[str]:
        """
        Download a PDF from a URL and save it to the PDF folder.

        Args:
            pdf_url: URL of the PDF to download
            patent_id: Patent ID to use as the filename

        Returns:
            Path to the downloaded PDF or None if download failed
        """
        try:
            # Clean the patent ID for use as a filename
            filename = f"{patent_id.replace('/', '_')}.pdf"
            filepath = os.path.join(self.pdf_folder_name, filename)

            # Check if the file already exists
            if os.path.exists(filepath):
                print(f"PDF for {patent_id} already exists at {filepath}")
                return filepath

            # Download the PDF
            print(f"Downloading PDF for {patent_id} from {pdf_url}")
            response = requests.get(pdf_url, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()

            # Save the PDF
            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"Successfully downloaded PDF for {patent_id} to {filepath}")
            return filepath

        except Exception as e:
            print(f"Error downloading PDF for {patent_id}: {str(e)}")
            return None

    def search_patents(self, smile: str, redis_host: str = None, redis_port: int = None,
                      redis_db: int = None) -> Tuple[Dict, List[str]]:
        """
        Main function to search for patents related to a SMILE string.
        Validates and normalizes patent IDs before querying.
        Only processes US patents and returns up to max_patents results.

        Args:
            smile: SMILE string to search for
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database

        Returns:
            Tuple of (search results dict, list of downloaded PDF paths)
        """
        # Use environment variables if parameters are not provided
        redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        redis_db = redis_db or int(os.getenv("REDIS_DB", 0))

        cleaned = self.clean_smile(smile)
        # Retrieve all patent IDs first
        all_patent_ids = self.get_patent_ids_from_redis(cleaned, redis_host, redis_port, redis_db)

        # Filter for US patents only
        us_patent_ids = [pid for pid in all_patent_ids if pid.upper().startswith("US")]
        print(f"Found {len(us_patent_ids)} US patents out of {len(all_patent_ids)} total patents")

        # Take only the first max_patents US patents
        us_patent_ids = us_patent_ids[:self.max_patents]

        results = []
        found_count = 0
        downloaded_pdfs = []

        # Process patents with a small delay between requests to avoid rate limiting
        for i, raw_id in enumerate(tqdm(us_patent_ids, desc="Processing patents")):
            # Normalize and standardize the patent ID
            pid = raw_id.upper()
            print(f"Processing US patent {i+1}/{len(us_patent_ids)}: {pid}")

            # Always attempt to get the PDF link, even if the format doesn't match our patterns
            pdf_url = self.get_patent_pdf_link(pid)

            if pdf_url:
                found_count += 1
                # Download the PDF
                pdf_path = self.download_pdf(pdf_url, pid)
                if pdf_path:
                    downloaded_pdfs.append(pdf_path)
                    status = "downloaded"
                else:
                    status = "download_failed"
            else:
                status = "not_found"

            results.append({
                "patent_id": pid,
                "pdf_link": pdf_url,
                "status": status
            })

            # Add a small delay between requests (except for the last one)
            if i < len(us_patent_ids) - 1:
                time.sleep(1.5)  # 1.5 second delay between requests to avoid rate limiting

        result_dict = {
            "smile": smile,
            "metadata": {
                "total_us_patents": len(us_patent_ids),
                "total_all_patents": len(all_patent_ids),
                "found": found_count,
                "downloaded": len(downloaded_pdfs),
                "not_found": len(us_patent_ids) - found_count,
            },
            "results": results
        }

        return result_dict, downloaded_pdfs

    def process_smile(self, smile: str, redis_host: str = None, redis_port: int = None,
                     redis_db: int = None) -> List[str]:
        """
        Process a SMILE string: search for patents, download PDFs, and return the list of downloaded PDFs.

        Args:
            smile: SMILE string to search for
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database

        Returns:
            List of paths to downloaded PDFs
        """
        print(f"Processing SMILE string: {smile}")
        result_dict, downloaded_pdfs = self.search_patents(smile, redis_host, redis_port, redis_db)

        # Save the results to a JSON file
        results_file = os.path.join(self.pdf_folder_name, f"patent_search_results_{smile.replace('/', '_')}.json")
        with open(results_file, 'w') as f:
            json.dump(result_dict, f, indent=2)

        print(f"Patent search results saved to {results_file}")
        print(f"Downloaded {len(downloaded_pdfs)} PDFs to {self.pdf_folder_name}")

        # Return full paths to the downloaded PDFs
        return [os.path.abspath(pdf) for pdf in downloaded_pdfs]


def main():
    """
    Main function to run the patent PDF downloader from the command line.
    """
    if len(sys.argv) < 2:
        print("Usage: python patentPDFDownloader.py <SMILE> [max_patents] [redis_host] [redis_port] [redis_db]")
        sys.exit(1)

    smile = sys.argv[1]

    # Command line arguments override environment variables
    max_patents = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    redis_host = sys.argv[3] if len(sys.argv) > 3 else os.getenv("REDIS_HOST", "localhost")
    redis_port = int(sys.argv[4]) if len(sys.argv) > 4 else int(os.getenv("REDIS_PORT", 6379))
    redis_db = int(sys.argv[5]) if len(sys.argv) > 5 else int(os.getenv("REDIS_DB", 0))

    downloader = PatentPDFDownloader(max_patents=max_patents)
    downloaded_pdfs = downloader.process_smile(smile, redis_host, redis_port, redis_db)

    print(f"Downloaded {len(downloaded_pdfs)} PDFs:")
    for pdf in downloaded_pdfs:
        print(f"  - {pdf}")


if __name__ == "__main__":
    main()
