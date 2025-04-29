# --- Add this block at the TOP of main.py ---
import ssl
import os

# WARNING: Disables SSL certificate verification globally!
# Use only if necessary and you understand the risks (e.g., trusted network).
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    print("!!! WARNING: SSL CERTIFICATE VERIFICATION DISABLED GLOBALLY !!!")
    ssl._create_default_https_context = ssl._create_unverified_context
# --- End of SSL bypass block ---

import json
from RetroSynAgent.treeBuilder import Tree, TreeLoader
from RetroSynAgent.pdfProcessor import PDFProcessor
from RetroSynAgent.knowledgeGraph import KnowledgeGraph
from RetroSynAgent import prompts
from RetroSynAgent.GPTAPI import GPTAPI
from RetroSynAgent.patentPDFDownloader import PatentPDFDownloader
from RetroSynAgent.pdfDownloader import PDFDownloader
from RetroSynAgent.name_to_smiles import NameToSMILES
import fitz  # PyMuPDF
import os
import json
import re
import pubchempy
from RetroSynAgent.entityAlignment import EntityAlignment
from RetroSynAgent.treeExpansion import TreeExpansion
from RetroSynAgent.reactionsFiltration import ReactionsFiltration
import argparse

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

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Process PDFs and extract reactions.")
    parser.add_argument('--material', type=str, required=True,
                        help="Chemical name or SMILES string of the target molecule (e.g., 'aspirin' or 'CC(=O)OC1=CC=CC=C1C(=O)O').")
    parser.add_argument('--num_results', type=int, required=True,
                        help="Maximum number of patent PDFs to download.")
    parser.add_argument('--alignment', type=str, default="False", choices=["True", "False"],
                        help="Whether to align entities except for root node.")
    parser.add_argument('--expansion', type=str, default="False", choices=["True", "False"],
                        help="Whether to expand the tree with additional literature.")
    parser.add_argument('--filtration', type=str, default="False", choices=["True", "False"],
                        help="Whether to filter reactions.")
    parser.add_argument('--retrieval_mode', type=str, default="patent-paper",
                        choices=["patent-patent", "paper-paper", "paper-patent", "patent-paper"],
                        help="Document retrieval mode: patent-patent (patents for both), paper-paper (papers for both), paper-patent (papers then patents), patent-paper (patents then papers)")
    return parser.parse_args()

def countNodes(tree):
    node_count = tree.get_node_count()
    return node_count

def searchPathways(tree):
    all_path = tree.find_all_paths()
    return all_path


def recommendReactions(prompt, result_folder_name, response_name):
    res = GPTAPI().answer_wo_vision(prompt)
    with open(f'{result_folder_name}/{response_name}.txt', 'w') as f:
        f.write(res)
    start_idx = res.find("Recommended Reaction Pathway:")
    recommend_reactions_txt = res[start_idx:]
    print(f'\n=================================================='
          f'==========\n{recommend_reactions_txt}\n====================='
          f'=======================================\n')
    return recommend_reactions_txt

def main(material,
        num_results,
        alignment,
        expansion,
        filtration,
        retrieval_mode="patent-paper"):
    # material = 'Polyimide'
    # num_results = 10
    # alignment = True
    # expansion = True
    # filtration = False

    # Parse command-line arguments
    # args = parse_arguments()
    # material = args.material
    # num_results = args.num_results
    # # turn str to bool
    # alignment = args.alignment == "True"
    # expansion = args.alignment == "True"
    # filtration = args.filtration == "True"

    try:
        print("Starting main function...")
        print(f"Material: {material}")
        print(f"Number of results: {num_results}")
        print(f"Alignment: {alignment}")
        print(f"Expansion: {expansion}")
        print(f"Filtration: {filtration}")
        print(f"Retrieval mode: {retrieval_mode}")

        pdf_folder_name = 'pdf_pi'
        result_folder_name = 'res_pi'
        result_json_name = 'llm_res'
        tree_folder_name = 'tree_pi'
        os.makedirs(tree_folder_name, exist_ok=True)
        entityalignment = EntityAlignment()
        treeloader = TreeLoader()
        tree_expansion = TreeExpansion()
        reactions_filtration = ReactionsFiltration()

        ### extractInfos

        # 1  Convert chemical name to SMILES if needed
        print(f"Processing material: {material}")
        smiles = material

        # Check if the input looks like a chemical name rather than a SMILES string
        if not re.search(r"[=#@\\/\[\]]|^[Cc][1-9]=|\.|\.\.\.|\.\.", material):
            print(f"Input appears to be a chemical name. Converting to SMILES...")
            success, result = NameToSMILES.convert(material)
            if success:
                smiles = result
                print(f"Successfully converted '{material}' to SMILES: {smiles}")
            else:
                print(f"Warning: Could not convert '{material}' to SMILES: {result}")
                print(f"Proceeding with the original input as SMILES.")
        else:
            print(f"Input appears to be a SMILES string already. Proceeding without conversion.")

        # 2  query literatures & download based on retrieval mode
        pdf_name_list = []

        # First part of retrieval mode determines initial document source
        if retrieval_mode.startswith("patent"):
            # Check if we have a valid SMILES string
            valid_smiles = True
            if not smiles or smiles == material:  # If conversion failed or wasn't attempted
                if not re.search(r"[=#@\\/\[\]]|^[Cc][1-9]=|\.|\.\.\.|\.\\..", smiles):
                    valid_smiles = False
                    print(f"Warning: '{smiles}' doesn't appear to be a valid SMILES string.")

            if valid_smiles:
                try:
                    print("Initializing PatentPDFDownloader for initial retrieval...")
                    downloader = PatentPDFDownloader(pdf_folder_name=pdf_folder_name, max_patents=num_results)
                    print("Calling process_smile method...")
                    pdf_name_list = downloader.process_smile(smiles)
                    print(f'Successfully downloaded {len(pdf_name_list)} PDFs from patents for SMILES: {smiles}')
                except ValueError as e:
                    print(f"Error with patent search: {str(e)}")
                    print("Falling back to academic paper search.")
                    # Fall back to academic paper search
                    print("Initializing PDFDownloader for initial retrieval (fallback)...")
                    os.makedirs(pdf_folder_name, exist_ok=True)
                    downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name, num_results=num_results, n_thread=3)
                    pdf_name_list = downloader.main()
                    print(f'Successfully downloaded {len(pdf_name_list)} PDFs from academic papers for {material}')
            else:
                # Fall back to academic paper search if no valid SMILES
                print("No valid SMILES string available. Using academic paper search instead.")
                print("Initializing PDFDownloader for initial retrieval...")
                os.makedirs(pdf_folder_name, exist_ok=True)
                downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name, num_results=num_results, n_thread=3)
                pdf_name_list = downloader.main()
                print(f'Successfully downloaded {len(pdf_name_list)} PDFs from academic papers for {material}')
        else:  # paper-based initial retrieval
            print("Initializing PDFDownloader for initial retrieval...")
            os.makedirs(pdf_folder_name, exist_ok=True)
            downloader = PDFDownloader(material, pdf_folder_name=pdf_folder_name, num_results=num_results, n_thread=3)
            pdf_name_list = downloader.main()
            print(f'Successfully downloaded {len(pdf_name_list)} PDFs from academic papers for {material}')

        if not pdf_name_list:
            print("No PDFs were downloaded. This could be because:")
            print("1. No patent IDs were found in Redis for this SMILES string")
            print("2. The patents found did not have downloadable PDFs")
            print("3. There was an error connecting to the patent database")
            print("\nPlease check that Redis is properly set up with patent data.")
            print("You can run the debug_downloader.py script to diagnose Redis issues.")
            return {"error": "No PDFs downloaded"}

        # 2 Extract infos from PDF about reactions
        pdf_processor = PDFProcessor(pdf_folder_name=pdf_folder_name, result_folder_name=result_folder_name,
                                     result_json_name=result_json_name)
        pdf_processor.load_existing_results()
        pdf_processor.process_pdfs_txt(save_batch_size=2)

        ### treeBuildWOExapnsion
        results_dict = entityalignment.alignRootNode(result_folder_name, result_json_name, material)

        # 4 construct kg & tree
        tree_name_wo_exp = tree_folder_name + '/' + material + '_wo_exp.pkl'
        if not os.path.exists(tree_name_wo_exp):
            tree_wo_exp = Tree(material.lower(), result_dict=results_dict)
            print('Starting to construct RetroSynthetic Tree...')
            tree_wo_exp.construct_tree()
            treeloader.save_tree(tree_wo_exp, tree_name_wo_exp)
        else:
            tree_wo_exp = treeloader.load_tree(tree_name_wo_exp)
            print('RetroSynthetic Tree wo expansion already loaded.')
        node_count_wo_exp = countNodes(tree_wo_exp)
        all_path_wo_exp = searchPathways(tree_wo_exp)
        print(f'The tree contains {node_count_wo_exp} nodes and {len(all_path_wo_exp)} pathways before expansion.')

        if alignment:
            print('Starting to align the nodes of RetroSynthetic Tree...')

            ### WO Expansion
            tree_name_wo_exp_alg = tree_folder_name + '/' + material + '_wo_exp_alg.pkl'
            if not os.path.exists(tree_name_wo_exp_alg):
                # reactions_wo_exp_alg = entityalignment.entityAlignment(tree_wo_exp.reactions)
                # tree_wo_exp_alg = Tree(material.lower(), reactions=reactions_wo_exp_alg)
                reactions_wo_exp = tree_wo_exp.reactions
                reactions_wo_exp_alg_1 = entityalignment.entityAlignment_1(reactions_dict=reactions_wo_exp)
                reactions_wo_exp_alg_all = entityalignment.entityAlignment_2(reactions_dict=reactions_wo_exp_alg_1)
                tree_wo_exp_alg = Tree(material.lower(), reactions=reactions_wo_exp_alg_all)
                tree_wo_exp_alg.construct_tree()
                treeloader.save_tree(tree_wo_exp_alg, tree_name_wo_exp_alg)
            else:
                tree_wo_exp_alg = treeloader.load_tree(tree_name_wo_exp_alg)
                print('aligned RetroSynthetic Tree wo expansion already loaded.')
            node_count_wo_exp_alg = countNodes(tree_wo_exp_alg)
            all_path_wo_exp_alg = searchPathways(tree_wo_exp_alg)
            print(f'The aligned tree contains {node_count_wo_exp_alg} nodes and {len(all_path_wo_exp_alg)} pathways before expansion.')
            # tree_wo_exp = tree_wo_exp_alg

        ## treeExpansion
        # 5 kg & tree expansion
        results_dict_additional = tree_expansion.treeExpansion(result_folder_name, result_json_name,
                                                               results_dict, material, expansion=expansion, max_iter=5,
                                                               retrieval_mode=retrieval_mode, smiles=smiles)
        if results_dict_additional:
            results_dict = tree_expansion.update_dict(results_dict, results_dict_additional)
            # results_dict.update(results_dict_additional)

        tree_name_exp = tree_folder_name + '/' + material + '_w_exp.pkl'
        if not os.path.exists(tree_name_exp):
            tree_exp = Tree(material.lower(), result_dict=results_dict)
            print('Starting to construct Expanded RetroSynthetic Tree...')
            tree_exp.construct_tree()
            treeloader.save_tree(tree_exp, tree_name_exp)
        else:
            tree_exp = treeloader.load_tree(tree_name_exp)
            print('RetroSynthetic Tree w expansion already loaded.')

        # nodes & pathway count (tree w exp)
        node_count_exp = countNodes(tree_exp)
        all_path_exp = searchPathways(tree_exp)
        print(f'The tree contains {node_count_exp} nodes and {len(all_path_exp)} pathways after expansion.')

        if alignment:
            ### Expansion
            tree_name_exp_alg = tree_folder_name + '/' + material + '_w_exp_alg.pkl'
            if not os.path.exists(tree_name_exp_alg):
                reactions_exp = tree_exp.reactions
                reactions_exp_alg_1 = entityalignment.entityAlignment_1(reactions_dict=reactions_exp)
                reactions_exp_alg_all = entityalignment.entityAlignment_2(reactions_dict=reactions_exp_alg_1)
                tree_exp_alg = Tree(material.lower(), reactions=reactions_exp_alg_all)
                tree_exp_alg.construct_tree()
                treeloader.save_tree(tree_exp_alg, tree_name_exp_alg)
            else:
                tree_exp_alg = treeloader.load_tree(tree_name_exp_alg)
                print('aligned RetroSynthetic Tree wo expansion already loaded.')
            node_count_exp_alg = countNodes(tree_exp_alg)
            all_path_exp_alg = searchPathways(tree_exp_alg)
            print(f'The aligned tree contains {node_count_exp_alg} nodes and {len(all_path_exp_alg)} pathways after expansion.')
            tree_exp = tree_exp_alg

        all_pathways_w_reactions = reactions_filtration.getFullReactionPathways(tree_exp)

        ## Filtration
        if filtration:
            # filter reactions based on conditions
            reactions_txt_filtered = reactions_filtration.filterReactions(tree_exp)
            # build & save tree
            tree_name_filtered = tree_folder_name + '/' + material + '_filtered' + '.pkl'
            if not os.path.exists(tree_name_filtered):
                print('Starting to construct Filtered RetroSynthetic Tree...')
                tree_filtered = Tree(material.lower(), reactions_txt=reactions_txt_filtered)
                tree_filtered.construct_tree()
                treeloader.save_tree(tree_filtered, tree_name_filtered)
            else:
                tree_filtered = treeloader.load_tree(tree_name_filtered)
                print('Filtered RetroSynthetic Tree already loaded.')
            node_count_filtered = countNodes(tree_filtered)
            all_path_filtered = searchPathways(tree_filtered)
            print(f'The tree contains {node_count_filtered} nodes and {len(all_path_filtered)} pathways after filtration.')

            # filter invalid pathways
            filtered_pathways = reactions_filtration.filterPathways(tree_filtered)
            all_pathways_w_reactions = filtered_pathways

        ### Recommendation
        # recommend based on specific criterion

        # [1]
        prompt_recommend1 = prompts.recommend_prompt_commercial.format(all_pathways = all_pathways_w_reactions, substance = material)
        recommend1_reactions_txt = recommendReactions(prompt_recommend1, result_folder_name, response_name='recommend_pathway1')
        parsed_data = parse_reaction_data(recommend1_reactions_txt)
        # tree_pathway1 = Tree(material.lower(), reactions_txt=recommend1_reactions_txt)
        # print('Starting to construct recommended pathway 1 ...')
        # tree_pathway1.construct_tree()
        # tree_name_pathway1 = tree_folder_name + '/' + material + '_pathway1' + '.pkl'
        # treeloader.save_tree(tree_pathway1, tree_name_pathway1)
        return parsed_data
    except Exception as e:
        import traceback
        print(f"Error in main function: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == '__main__':
    try:
        args = parse_arguments()
        material = args.material
        num_results = args.num_results
        alignment = args.alignment == "True"
        expansion = args.expansion == "True"
        filtration = args.filtration == "True"
        retrieval_mode = args.retrieval_mode

        print(f"Running with parameters: material={material}, num_results={num_results}, alignment={alignment}, expansion={expansion}, filtration={filtration}, retrieval_mode={retrieval_mode}")

        result = main(
            material,
            num_results,
            alignment,
            expansion,
            filtration,
            retrieval_mode
        )
        print("Program completed successfully!")
    except Exception as e:
        import traceback
        print(f"Error in __main__: {str(e)}")
        traceback.print_exc()
