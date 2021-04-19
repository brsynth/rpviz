# apprpviz
Apps for remote access to the pathway visualizer.

## Important

Input file expected by the viewer:
- `network.json`: should contains 2 variable, namely `network` and
`pathways_info`.

## Execute

From a given -- and compatible -- rpSBML tar file:
```
python -m rpviz.cli rpSBML.tar outfolder
```

## Setting up

Below are instructions to set up a conda environment. This is still in development.

```bash
conda create -n rpviz
source activate rpviz
conda install -y -c rdkit rdkit
conda install -y -c bioconda python-libsbml
conda install -y -c bioconda pubchempy
conda install -y -c conda-forge lxml
conda install -y -c conda-forge requests
conda install -y -c conda-forge cirpy
conda install -y -c conda-forge networkx
conda install -y -c conda-forge beautifulsoup4
conda install -y -c conda-forge matplotlib
```

## JSON objects


### network

Below an overview of the `network` object expected by the JS viewer:

```json
{
    "elements": {
        "nodes": [
            {
                "data": {
                    "id": "string",
                    "path_ids": ["string"],
                    "type": "reaction",
                    "label": "string",
                    "all_labels": ["string"],
                    "svg": "string",
                    "xlinks": [{"db_name":  "string", "entity_id": "string", "url": "string"}, ...],
                    "rsmiles": "string",
                    "rule_id": "string",
                    "fba_reaction": integer,
                    "smiles": null,
                    "inchi": null,
                    "inchikey": null,
                    "target_chemical": null,
                    "cofactor": null
                }
            },
            ...,
            ...,
            ...,
            {
                "data": {
                    "id": "string",
                    "path_ids": ["string"],
                    "type": "chemical",
                    "label": "string",
                    "all_labels": ["string"],
                    "svg": "string",
                    "xlinks": [{"db_name":  "string", "entity_id": "string", "url": "string"}, ...],
                    "rsmiles": null,
                    "rule_id": null,
                    "fba_reaction": null,
                    "smiles": "string",
                    "inchi": "string",
                    "inchikey": "string",
                    "target_chemical": integer,
                    "cofactor": integer
                }
            },
            ...
            ...
            ...
        ],
        "edges": [
            {
                "data": {
                    "id": "string",
                    "path_ids": ["string"],
                    "source": "string",
                    "target": "string"
                }
            },
            ...
            ...
            ...
        ]
    }
}
```

`network` is composed of 2 types of nodes ("reaction" and "chemical"), and 1 type of edge. What ever the node type,
all the keys ('id', 'path_ids', ...) should be present in each node.


#### reaction node

For reaction node, the content should be: 

- `id`, (string), __required value__ -- The canonic reaction SMILES of the reactions. It will be use as the
unique ID of the node. Example: `"id": "[H]OC(=O)C([H])=C([H])C([H])=C([H])C(=O)O[H]>>O=O.[H]Oc1c([H])c([H])c([H])c([H])c1O[H]"`
- `path_ids`: (list of strings), __required values__ -- The list of unique pathway IDs into which the reaction
is involved. It should not contains duplicates. Example: `"path_ids": ["rp_3_1", "rp_2_1", "rp_3_2", "rp_1_1"]`
- `type`, (string), __required value__ -- Should be `"reaction"` for reaction node. It is this value that define
the type of node.
- `label`, (string), __required value__ -- The label to be printed for the node.
- `all_labels`, (list of strings), __optional__ -- All possible labels for the node.
- `svg`, (string), __required__ -- SVG depiction of the reaction.
- `xlinks` (list of dictionaries), __optional__ -- Crosslinks to the reaction. Each individual crosslink should
be described in a dictionary having keys: "db_name", "entity_id", "url".   
- `rsmiles`, (string), __optional__ -- The canonical reaction SMILES.
- `rule_id`, (string), __optional__ -- The reaction rule ID. 
- `fba_reaction`, (string), __optional__ -- Flag to designate the FVA output reaction that consume the target.
Should be either 0 (this is not such reaction) or 1 (this is).
- `smiles`, (string), __not used__ -- Value should be `null` (meaningful for chemical node only).
- `inchi`, (string),  __required value__ -- Value should be `null`.
- `inchikey`, (string),  __required value__ -- Value should be `null`.
- `target_chemical`, (string), __not used__ -- Value should be `null`.
- `cofactor`, (string), __not used__ -- Value should be `null`.

#### chemical node

For chemical node, the content should be:

- `id`, (string), __required value__ -- The InChIKey of the chemical. It will be use as the unique ID of the node.
- `path_ids`: (list of strings), __required values__ -- The list of unique pathway IDs into which the chemical is
involved. It should not contains duplicates. Example: `"path_ids": ["rp_3_1", "rp_2_1", "rp_3_2", "rp_1_1"]`
- `type`, (string), __required value__ -- Should be `"chemical"` for chemical node. It is this value that define the
type of node.
- `label`, (string), __required value__ -- The label to be printed for the node.
- `all_labels`, (list of strings), __optional__ -- All possible labels for the node.
- `svg`, (string),   __required value__ -- SVG depiction of the chemical.
- `xlinks` (list of dictionaries), __optional__ -- Crosslinks to the chemical. Each individual crosslink should
be described in a dictionary having keys: "db_name", "entity_id", "url".
- `rsmiles`, (string), __not used__ -- Value should be `null` (meaningful for reaction node only).
- `rule_id`, (string), __not used__ -- Value should be `null`.
- `fba_reaction`, (string), __not used__ -- Value should be `null`.
- `smiles`, (string), __required value__ -- The canonic SMILES.
- `inchi`, (string),  __required value__ -- InChI.
- `inchikey`, (string),  __required value__ -- InChIKey.
- `target_chemical`, (string), __required__ -- Flag to designate the target. Value should be either 0 (not the
target) or 1 (it is).
- `cofactor`, (string), __required__ -- Flag to designate cofactor chemicals (eg: ATP, NADH, ...). Value should
be either 0 (not a cofactor) or 1 (it is).


#### edge

For edge, the content should be:

- `id`, (string), __required value__ -- Some unique string to be used as edge ID. To build such ID, follow the 
convention: `A_B` where `A` is the source node ID (eg a chemical node ID) and `B` is the target node ID (eg 
a reaction node ID).
- `path_ids`: (list of strings), __required values__ -- The list of unique pathway IDs into which the edge is
involved in.
- `source`: the source node ID.
- `target`: the target node ID.

### pathways_info

The pathway_info JSON object purpose is to store information related to each pathways. Notice that order of 
pathway matter: the JS viewer will print the pathways in the order they are given in this object. Here is
the content:
```json
{
    "path_id1": {
        "path_id": "path_id1",
        "node_ids": ["node_id1", "node_id2", ...],
        "edge_ids": ["edge_id1", "edge_id2", ...],
        "scores": {
            "score_type_1": normalised integer,
            "score_type_2": normalised integer,
            ...
        }
    },
    "path_id2": {...},
    ...
    ...
    ...
}
```

Where:
- `path_id` is the pathway ID,
- `node_ids` and `edge_ids` lists the nodes and edges involved in this pathway,
- `scores` gives the pathway scores.


## Implementation choices

- If a compound cannot be associated to an inchikey (typically, in the case of a generic compound like
`NAD-OR-NADP`), then the MNX ID is used as ID in the network.json file. If no MNX is available, then an
error is logged and the execution is continued.

- rpSBML file name should end by `.sbml.xml`

- Target chemical should be have a SBML name that starts by `TARGET`


## Known bugs and feature requests

- Add EC number annotations into the JSON network outputted
- Add annotation about if a chemical is in sink
- Add crosslinks for sequences
- Add crosslinks for reactions
- Add thermodynamics information for chemical, reaction (`network` dictionary) and pathways (`pathway_info` dictionary)
- Add the pathway scores
- Provide the good URLs for crosslinks, not those pointing to identifiers.org
