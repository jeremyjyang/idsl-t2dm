-- See https://neo4j.com/docs/getting-started/current/cypher-intro/load-csv/
-- "MATCH (n) DELETE n" deletes all nodes.
-- "MATCH (n) DETACH DELETE n" deletes all nodes and relationships.
-- Load SLAP results linking drugs and targets from Google Sheets.


-- Compounds:
LOAD CSV WITH HEADERS
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/slap_dtp_merged_nodes_compounds.tsv"
	AS csvLine
	FIELDTERMINATOR '\t'
CREATE
	(c:Compound {
		CID: csvLine.PUBCHEM_COMPOUND_CID,
		name:csvLine.PUBCHEM_IUPAC_TRADITIONAL_NAME,
		smiles:csvLine.PUBCHEM_OPENEYE_CAN_SMILES})
	;

-- Genes:
LOAD CSV WITH HEADERS
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/slap_dtp_merged_nodes_genes.tsv"
	AS csvLine
	FIELDTERMINATOR '\t'
CREATE
	(g:Gene {
		gene_symbol: csvLine.Gene
		})
	;

-- Compound-Genes (chemogenomic) edges:
USING PERIODIC COMMIT 500
LOAD CSV WITH HEADERS
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/slap_dtp_merged_edges_chemogenomic.tsv"
	AS csvLine 
MATCH
	(c:Compound {CID:csvLine.CID}),
	(g:Gene {gene_symbol:csvLine.Gene})
CREATE (c)-[:chemogenomic {
		name:csvLine.name,
		evidence:csvLine.evidence,
		weight:toFloat(csvLine.weight)}
	]->(g)
	;

-- Proteins:
LOAD CSV WITH HEADERS
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/protein_list.csv"
	AS csvLine
CREATE
	(p:Protein {
		UniprotID:csvLine.protein_accession,
		name:csvLine.name})
	;


-- Other Cytoscape classes:


-- Diabetes Drugs:
LOAD CSV
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/diabetes_drugs.smi"
	AS csvLine
CREATE
	(d:Drug {
		smiles:csvLine[0],
		name:csvLine[1],
		CID:csvLine[2]})
	;

-- SLAP Compound-Target Associations:
USING PERIODIC COMMIT 500
LOAD CSV WITH HEADERS
FROM "https://raw.githubusercontent.com/IUIDSL/t2d-net/master/data/t2d_dtp_links.csv" 
	AS csvLine 
MATCH
	(c:Compound {CID:csvLine.CID}),
	(p:Protein {UniprotID:csvLine.TID})
CREATE (c)-[:SLAP {
		score_type: csvLine.score_type,
		score_note: csvLine.score_note,
		score: toFloat(csvLine.score)}
	]->(p)
	;
