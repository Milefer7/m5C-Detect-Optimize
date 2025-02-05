import argparse
from Bio import SeqIO

# python extract_rrna_trna.py Homo_sapiens.GRCh38.ncrna.fa rRNA.fa tRNA.fa
def extract_rrna_trna(input_fasta, output_rrna, output_trna):
    rrna_records = []
    trna_records = []
    
    for record in SeqIO.parse(input_fasta, "fasta"):
        description = record.description.lower()
        if "gene_biotype:rrna" in description or "transcript_biotype:rrna" in description or "gene_biotype:mt_rrna" in description or "transcript_biotype:mt_rrna" in description:
            rrna_records.append(record)
        elif "gene_biotype:mt_trna" in description or "transcript_biotype:mt_trna" in description:
            trna_records.append(record)
    
    SeqIO.write(rrna_records, output_rrna, "fasta")
    SeqIO.write(trna_records, output_trna, "fasta")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract rRNA and tRNA sequences from a combined ncRNA FASTA file.')
    parser.add_argument('input_fasta', help='Input combined ncRNA FASTA file')
    parser.add_argument('output_rrna', help='Output rRNA FASTA file')
    parser.add_argument('output_trna', help='Output tRNA FASTA file')
    args = parser.parse_args()
    extract_rrna_trna(args.input_fasta, args.output_rrna, args.output_trna)
