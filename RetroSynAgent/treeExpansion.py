import os
import copy
import json
import re
from . import prompts
from .treeBuilder import Tree, TreeLoader
from .pdfDownloader import PDFDownloader
from .pdfProcessor import PDFProcessor
from .GPTAPI import GPTAPI


class TreeExpansion:
    def update_json_file(self, add_results_filepath, add_results):
        # If the file exists, read the file content first
        if os.path.exists(add_results_filepath):
            with open(add_results_filepath, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}  # Initialize as an empty dictionary if the file is empty or corrupted
        else:
            existing_data = {}
        # Update existing data
        existing_data.update(add_results)
        existing_data = self.update_dict(existing_data, add_results)

        # Write the updated data back to the file
        with open(add_results_filepath, 'w') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)

    def update_dict(self, dict_1, dict_2):
        dict1 = dict_1.copy()
        dict2 = dict_2.copy()
        for key, value in dict2.items():
            if key not in dict1:
                dict1[key] = value
        return dict1

    def expand_reactions_from_literature(self, result_folder_name, result_json_name, material, origin_result_dict, max_iter=10, retrieval_mode="patent-paper", smiles=None):
        add_results_filepath = result_folder_name + '/' + result_json_name + '_add.json'
        literature_add_folder = 'pdf_add'
        os.makedirs(literature_add_folder, exist_ok=True)
        result_dict = copy.deepcopy(origin_result_dict)
        # additional_reactions_txt = ''
        add_results_new = {}
        result = False
        unexpandable_substances = set()
        iteration = 1
        # Exit the while loop if result is true and unexpandable_substances is an empty set.
        # Enter the loop if result is false or unexpandable_substances is not an empty set.

        while not result or unexpandable_substances:
            print(f'Iteration: {iteration}')
            # 3. build graph & tree
            # tree = Tree(material.lower(), reactions_txt=reactions_text)
            if add_results_new:
                # result_dict.update(add_results_new)
                result_dict = self.update_dict(result_dict, add_results_new)
            tree = Tree(material.lower(), result_dict = result_dict)
            result = tree.construct_tree()

            if tree.unexpandable_substances != set():
                unexp_subs_list = list(tree.unexpandable_substances)  # set -> list
                print(f"Unexpandable substances: {', '.join(unexp_subs_list)}")
                print(f'Now search for additional literature on these unexpandable intermediates.')
                for substance in unexp_subs_list:
                    pdf_name_list = []
                    attempt_iter = 0
                    pdf_folder_path = f'{literature_add_folder}/pdf_add_' + substance

                    # # num of pdf in pdf_folder_path is 0
                    # if (not os.path.exists(pdf_folder_path)) or (len(os.listdir(pdf_folder_path)) == 0):
                    #     while len(pdf_name_list) == 0:
                    #         attempt_iter += 1
                    #         downloader = PDFDownloader(substance, pdf_folder_name=pdf_folder_path,
                    #                                    num_results=attempt_iter, n_thread=3)
                    #         pdf_name_list = downloader.main()
                    #         if attempt_iter >= 3:
                    #             print(f'Fail to download additional PDFs for {substance} after 3 attempts.')
                    #             break
                    #     print(f'Successfully downloaded {len(pdf_name_list)} PDFs for {substance}')
                    # # num of pdf in pdf_folder_path is not 0
                    # else:
                    #     # Traverse all files in the folder
                    #     for file_name in os.listdir(pdf_folder_path):
                    #         # Check if the file extension is .pdf
                    #         if file_name.endswith(".pdf"):
                    #             pdf_name_list.append(file_name)

                    if not os.path.exists(pdf_folder_path):
                        os.makedirs(pdf_folder_path, exist_ok=True)

                    # If the number of PDFs in the folder is less than 3, try downloading
                    while len(os.listdir(pdf_folder_path)) < 3 and attempt_iter < 3:
                        attempt_iter += 1

                        # Second part of retrieval_mode determines expansion document source
                        if retrieval_mode.endswith("patent"):
                            # Use patent downloader for expansion
                            from .patentPDFDownloader import PatentPDFDownloader
                            from .name_to_smiles import NameToSMILES

                            # Try to convert substance name to SMILES
                            valid_smiles = False
                            substance_smiles = substance

                            # Check if it already looks like a SMILES string
                            if re.search(r"[=#@\\/\[\]]|^[Cc][1-9]=|\.|\.\.\.|\.\\..", substance):
                                valid_smiles = True
                            else:
                                # Try to convert to SMILES
                                print(f"Converting {substance} to SMILES for patent search...")
                                success, result = NameToSMILES.convert(substance)
                                if success:
                                    substance_smiles = result
                                    valid_smiles = True
                                    print(f"Successfully converted '{substance}' to SMILES: {substance_smiles}")
                                else:
                                    print(f"Warning: Could not convert '{substance}' to SMILES: {result}")
                                    print(f"Cannot use patent search for this substance. Falling back to academic paper search.")
                                    valid_smiles = False

                            # Only use PatentPDFDownloader if we have a valid SMILES
                            if valid_smiles:
                                try:
                                    downloader = PatentPDFDownloader(pdf_folder_name=pdf_folder_path, max_patents=attempt_iter)
                                    pdf_name_list = downloader.process_smile(substance_smiles)
                                    print(f"Downloaded {len(pdf_name_list)} patent PDFs for expansion of {substance}")
                                except ValueError as e:
                                    print(f"Error with patent search: {str(e)}")
                                    print("Falling back to academic paper search.")
                                    # Fall back to academic paper search
                                    downloader = PDFDownloader(substance, pdf_folder_name=pdf_folder_path,
                                                           num_results=attempt_iter, n_thread=3)
                                    pdf_name_list = downloader.main()
                                    print(f"Downloaded {len(pdf_name_list)} academic paper PDFs for expansion of {substance}")
                            else:
                                # Fall back to academic paper search if no valid SMILES
                                downloader = PDFDownloader(substance, pdf_folder_name=pdf_folder_path,
                                                       num_results=attempt_iter, n_thread=3)
                                pdf_name_list = downloader.main()
                                print(f"Downloaded {len(pdf_name_list)} academic paper PDFs for expansion of {substance}")
                        else:
                            # Use academic paper downloader for expansion
                            downloader = PDFDownloader(substance, pdf_folder_name=pdf_folder_path,
                                                       num_results=attempt_iter, n_thread=3)
                            pdf_name_list = downloader.main()
                            print(f"Downloaded {len(pdf_name_list)} academic paper PDFs for expansion of {substance}")

                    # Determine whether the download is successful based on the last file number
                    if len(os.listdir(pdf_folder_path)) < 3:
                        print(f'Fail to download at least 3 PDFs for {substance} after {attempt_iter} attempts.')
                    else:
                        print(f'Successfully downloaded {len(os.listdir(pdf_folder_path))} PDFs for {substance}')

                    # If there are (or newly downloaded) at least 3 PDFs, you can process them further
                    # if len(os.listdir(pdf_folder_path)) >= 3:
                    # for file_name in os.listdir(pdf_folder_path):
                    #     if file_name.endswith(".pdf"):
                    #         pdf_name_list.append(file_name)

                    # ========================================================================================

                    # get pdfs in pdf_folder_path (either new-downloaded or original)
                    for pdf_name in pdf_name_list:
                        pdf_name_wo_suffix = pdf_name.replace('.pdf', '')
                        try:
                            with open(add_results_filepath, 'r') as f:
                                origin_add_results = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError):
                            origin_add_results = {}
                        if pdf_name_wo_suffix not in origin_add_results:
                            # Ensure we don't duplicate the path
                            if pdf_name.startswith(pdf_folder_path):
                                pdf_path = pdf_name
                            else:
                                pdf_path = os.path.join(pdf_folder_path, pdf_name)
                            # pdf_path = 'literature_add_folder/pdf_add_substancesName/literatureTitle.pdf'
                            pdf_processor = PDFProcessor()
                            long_string = pdf_processor.pdf_to_long_string(pdf_path)
                            total_length = len(long_string)
                            print(f'Processing: {pdf_name_wo_suffix}, TXT Length: {total_length}')
                            prompt = prompts.prompt_add_reactions_from_literature_cot.format(material=substance)
                            llm = GPTAPI()
                            response = llm.answer_wo_vision(prompt, content=long_string)
                            #
                            ans_reaction = pdf_processor.replace_zeros_in_reactants_and_products(response)
                            ans_reaction = ans_reaction.split("Final Output:")[-1].strip()
                            add_results_new[pdf_name_wo_suffix] = ans_reaction
                            # update add results json file
                            self.update_json_file(add_results_filepath, add_results_new)
                        else:
                            print(f'{pdf_name_wo_suffix} has been processsed.')

                iteration += 1
                if iteration == max_iter:
                    print('exit loop because exceed max iteration')
                    break
            # else: unexpandable_substances == set()
            else:
                # If there are no unexpanded substances, set unexpandable_substances to an empty set
                # This is the key to exiting the loop
                unexpandable_substances = set()

                print('exit loop because set is empty')
        return add_results_new


    def treeExpansion(self, result_folder_name, result_json_name, results_dict, material, expansion=False, max_iter=10, retrieval_mode="patent-paper", smiles=None):
        add_results_filepath = result_folder_name + '/' + result_json_name + '_add.json'
        if os.path.exists(add_results_filepath):
            with open(add_results_filepath, 'r') as file:
                add_results = json.load(file)
                # results_dict.update(add_results)
                results_dict = self.update_dict(results_dict, add_results)
            print(f'Total: {len(results_dict)} articles.')
        else:
            add_results = {}
            print('Failed to load additional reaction data. File path does not exist.')

        if expansion:
            print('Starting expansion of the RetroSynthetic tree...')
            # note: key step expand to full
            add_results_new = self.expand_reactions_from_literature(result_folder_name, result_json_name, material,
                                                                    origin_result_dict = results_dict,
                                                                    max_iter = max_iter,
                                                                    retrieval_mode = retrieval_mode,
                                                                    smiles = smiles)
            if add_results_new:
                # add_results.update(add_results_new)
                add_results = self.update_dict(add_results, add_results_new)
        return add_results
