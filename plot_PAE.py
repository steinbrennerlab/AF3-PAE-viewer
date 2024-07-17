#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import traceback

def create_output_folder(base_folder, peptide_sequence, residues):
    residue_str = '_'.join(map(str, residues))
    folder_name = f"PAE-{peptide_sequence}_{residue_str}"
    output_folder = os.path.join(base_folder, folder_name)
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

def process_json_file(file_path, peptide_sequence, residues, combined_pdf, output_folder):
    try:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        outfile = os.path.join(output_folder, f"{base_name}.pdf")
        outfile2 = os.path.join(output_folder, f"{base_name}_residue.pdf")
        outfile3 = os.path.join(output_folder, f"{base_name}_reciprocal_residue.pdf")
        peptide_length = len(peptide_sequence)

        # Read the JSON file
        with open(file_path, 'r') as file:
            json_data = json.load(file)

        # Extract PAE data
        pae_data = pd.DataFrame(json_data['pae'])
        pae_data2 = pd.DataFrame(json_data['pae'])

        # Plot PAE values for all residues
        plt.figure(figsize=(10, 6))
        for n in range(peptide_length):
            plt.plot(pae_data.iloc[n], label=n+1)
        plt.title(f"{os.path.basename(file_path)}\nPeptide: {peptide_sequence}")
        plt.xlabel("Residue")
        plt.ylabel("PAE")
        plt.legend(loc="upper left", bbox_to_anchor=(1,1))
        plt.axvline(x=peptide_length, color="black")
        plt.savefig(outfile, format="pdf")
        plt.close()

        # Plot PAE values for specific residues and reciprocal PAE values
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
        
        for n in residues:
            ax1.plot(pae_data.iloc[int(n)-1], label=peptide_sequence[int(n)-1]+str(n))
        ax1.set_title(f"Standard PAE - {os.path.basename(file_path)}\nPeptide: {peptide_sequence}")
        ax1.set_xlabel("Residue")
        ax1.set_ylabel("PAE")
        ax1.legend(loc="upper left", bbox_to_anchor=(1,1))
        ax1.axvline(x=peptide_length, color="black")
        
        for n in residues:
            ax2.plot(pae_data2.iloc[:,int(n)-1], label=peptide_sequence[int(n)-1]+str(n))
        ax2.set_title(f"Reciprocal PAE - {os.path.basename(file_path)}\nPeptide: {peptide_sequence}")
        ax2.set_xlabel("Residue")
        ax2.set_ylabel("PAE")
        ax2.legend(loc="upper left", bbox_to_anchor=(1,1))
        ax2.axvline(x=peptide_length, color="black")
        
        plt.tight_layout()
        combined_pdf.savefig(fig)
        plt.close(fig)

        # Save individual plots
        fig.savefig(outfile2, format="pdf", bbox_inches="tight")
        fig.savefig(outfile3, format="pdf", bbox_inches="tight")

        # Calculate minimum PAE values
        pae_minima = []
        labels = []
        residues_list = []
        for n in range(peptide_length):
            exclude_n_term_length = peptide_length
            array = pae_data.iloc[n]
            modified_array = array[exclude_n_term_length:]
            min_value = min(modified_array)
            aminoacid = peptide_sequence[n]
            residues_list.append(aminoacid)
            labels.append(str(n+1))
            pae_minima.append(min_value)

        df = pd.DataFrame({
            'residue_num': labels,
            'residues': residues_list,
            base_name: pae_minima
        })
        
        df.to_csv(os.path.join(output_folder, f"{base_name}_pae_minima.csv"), index=False)
        
        # Calculate and save minimum reciprocal PAE scores for peptide sequence
        reciprocal_pae_minima = []
        for n in range(peptide_length):
            exclude_n_term_length = peptide_length
            array = pae_data2.iloc[:,int(n)]
            modified_array = array[exclude_n_term_length:]
            min_value = min(modified_array)
            reciprocal_pae_minima.append(min_value)
        
        reciprocal_pae_df = pd.DataFrame({
            'residue_num': labels,
            'residues': residues_list,
            f'{base_name}_reciprocal_min': reciprocal_pae_minima
        })
        
        reciprocal_pae_df.to_csv(os.path.join(output_folder, f"{base_name}_reciprocal_pae_minima.csv"), index=False)
        
        return df, reciprocal_pae_df

    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        traceback.print_exc()
        return None, None

def create_combined_csv(all_data, output_folder):
    combined_df = pd.DataFrame()
    for df in all_data:
        if combined_df.empty:
            combined_df = df[['residue_num', 'residues']]
        combined_df = pd.merge(combined_df, df, on=['residue_num', 'residues'], how='outer')
    
    combined_csv_path = os.path.join(output_folder, "combined_pae_minima.csv")
    combined_df.to_csv(combined_csv_path, index=False)
    print(f"Combined CSV saved as: {combined_csv_path}")

def create_combined_reciprocal_pae(all_reciprocal_data, output_folder):
    combined_reciprocal_df = pd.concat(all_reciprocal_data, axis=1, keys=range(len(all_reciprocal_data)))
    combined_reciprocal_csv_path = os.path.join(output_folder, "combined_reciprocal_pae.csv")
    combined_reciprocal_df.to_csv(combined_reciprocal_csv_path)
    print(f"Combined reciprocal PAE CSV saved as: {combined_reciprocal_csv_path}")

def main():
    parser = argparse.ArgumentParser(description='Analyze JSON files from Alphafold output in a folder')
    parser.add_argument("folder", help="folder containing json files to analyze")
    parser.add_argument("peptide", help="sequence in amino acids of the N-terminal peptide")
    parser.add_argument("residues", nargs='*', type=int, default=[1, 2, 3], help="residues to plot individually")
    args = parser.parse_args()

    folder_path = args.folder
    peptide_sequence = str(args.peptide)
    residues = args.residues

    output_folder = create_output_folder(folder_path, peptide_sequence, residues)
    combined_pdf_path = os.path.join(output_folder, "combined_plots.pdf")
    all_data = []
    all_reciprocal_data = []
    
    try:
        with PdfPages(combined_pdf_path) as combined_pdf:
            json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
            for i, filename in enumerate(json_files):
                file_path = os.path.join(folder_path, filename)
                print(f"Processing file: {file_path}")
                df, reciprocal_df = process_json_file(file_path, peptide_sequence, residues, combined_pdf, output_folder)
                if df is not None and reciprocal_df is not None:
                    all_data.append(df)
                    all_reciprocal_data.append(reciprocal_df)
            
            if len(json_files) == 0:
                print("No JSON files found in the specified folder.")
            else:
                print(f"Combined PDF saved as: {combined_pdf_path}")
                print(f"All output files saved in: {output_folder}")
                
                create_combined_csv(all_data, output_folder)
                create_combined_reciprocal_pae(all_reciprocal_data, output_folder)
    except Exception as e:
        print(f"Error creating combined PDF: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()