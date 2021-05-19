#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""cli.py: CLI for generating the JSON file expected by the pathway visualiser."""

__author__ = 'Thomas Duigou'
__license__ = 'MIT'

import os
import csv
import glob
import logging

from statistics import mean
from collections import OrderedDict

# from rpSBML import rpSBML as old_rpSBML
from rptools.rplibs import rpSBML

DEBUG = True

miriam_header = {
    'compartment': {
        'go': 'go/GO:',
        'mnx': 'metanetx.compartment/',
        'bigg': 'bigg.compartment/',
        'seed': 'seed/',
        'name': 'name/'
    },
    'reaction': {
        'metanetx': 'metanetx.reaction/',
        'rhea': 'rhea/',
        'reactome': 'reactome/',
        'bigg': 'bigg.reaction/',
        'sabiork': 'sabiork.reaction/',
        'ec-code': 'ec-code/',
        'biocyc': 'biocyc/', 'lipidmaps': 'lipidmaps/'
    },
    'species': {
        'metanetx': 'metanetx.chemical/',
        'chebi': 'chebi/CHEBI:',
        'bigg': 'bigg.metabolite/',
        'hmdb': 'hmdb/',
        'kegg_c': 'kegg.compound/',
        'kegg_d': 'kegg.drug/',
        'biocyc': 'biocyc/META:',
        'seed': 'seed.compound/',
        'metacyc': 'metacyc.compound/',
        'sabiork': 'sabiork.compound/',
        'reactome': 'reactome/R-ALL-'
    }
}


def _specie_is_target(specie_id):
    """Detect is a specie should be considered as a target

    FIXME, this needs to be refined so that we don't rely on the specie ID.

    :param specie_id: specie ID
    :type: str
    :return: true if it is a target, otherwise false
    :rtype: bool
    """
    if specie_id.startswith('TARGET_'):
        return True
    return False


def _specie_is_intermediate(specie_id, specie_dict=None):
    """Detect is a specie should be considered as an intermediate compound.

    FIXME, this needs to be refined so that we don't rely on the specie ID.

    :param specie_id: specie ID
    :type: str
    :param specie_dict: dictionary about the specie
    :type specie_dict: dict
    :return: true if it is, otherwise false
    :rtype: bool
    """
    if specie_id.startswith('CMPD_'):
        return True
    return False


def _specie_is_sink(specie_id, specie_dict=None):
    """Detect is a specie should be considered as a sink

    FIXME, this needs to be refined so that we don't rely on the specie ID.

    :param specie_id: specie ID
    :type: str
    :param specie_dict: dictionary about the specie
    :type specie_dict: dict
    :return: true if it is, otherwise false
    :rtype: bool
    """
    if not _specie_is_target(specie_id) and not _specie_is_intermediate(specie_id):
        return True
    return False


def _get_pathway_scores(pathway_dict):
    """Return pathway scores as a dictionary of scores

    :param pathway_dict: pathway dictionary as output by toDict
    :type: dict
    :return: dictionary of scores
    :rtype: dict
    """
    __SCORE_KEYS = [
        'norm_fba_obj_biomass',
        'norm_fba_obj_fraction',
        'norm_rule_score',
        'norm_steps',
        'global_score'
    ]
    scores = {}
    for score_type in __SCORE_KEYS:
        try:
            scores[score_type] = pathway_dict['brsynth'][score_type]
        except KeyError:
            logging.warning(f'Cannot retrieve pathway score "{score_type}" in rpSBML. Set to None')
            scores[score_type] = None
    return scores


def _get_pathway_thermo(pathway_dict):
    try:
        return pathway_dict['brsynth']['dfg_prime_m']['value']
    except KeyError:
        return None


def _get_pathway_fba(pathway_dict):
    try:
        return pathway_dict['brsynth']['fba_obj_fraction']['value']
    except KeyError:
        return None


def _get_reaction_node_id(rxn_dict):
    """Return a useful ID for the reaction node.

    A reaction node could be shared between several pathways, the reaction SMILES is an easy
    way to detect identical reactions used by different pathways.
    """
    if _get_reaction_smiles(rxn_dict) is not None:
        return rxn_dict['brsynth']['smiles']
    else:
        raise NotImplementedError(f'Cannot assign a valid ID to reaction idx {rxn_dict["rxn_idx"]} ')


def _get_reaction_ecs(rxn_dict):
    if 'ec-code' in rxn_dict['miriam'] \
            and len(rxn_dict['miriam']['ec-code']):
        return rxn_dict['miriam']['ec-code']
    else:
        return []


def _get_reaction_thermo(rxn_dict):
    if 'dfG_prime_m' in rxn_dict['brsynth']:
        return rxn_dict['brsynth']['dfG_prime_m']
    else:
        return None


def _get_reaction_labels(rxn_dict):
    if len(_get_reaction_ecs(rxn_dict)):
        return [*_get_reaction_ecs(rxn_dict)]
    else:
        return [rxn_dict['brsynth']['rule_id'],]


def _get_reaction_smiles(rxn_dict):
    if 'smiles' in rxn_dict['brsynth'] \
            and rxn_dict['brsynth']['smiles'] is not None \
            and rxn_dict['brsynth']['smiles'] != '':
        return rxn_dict['brsynth']['smiles']
    else:
        return None


def _get_reaction_xlinks(rxn_dict):
    # TODO refine this method
    xlinks = []
    # Special case for EC numbers
    for ec in _get_reaction_ecs(rxn_dict):
        # Get rid of unwanted characters
        ec_tmp = []
        for digit in ec.split('.'):
            if digit in '-_' or digit == '':
                break
            ec_tmp.append(digit)
        ec_refined = '.'.join(ec_tmp)
        if ec != ec_refined:
            logging.info(f'Refined EC number from {ec} to {ec_refined}')
        # Use direct link to workaround generic ECs issue with identifiers.org
        xlinks.append({
            'db_name': 'intenz',
            'entity_id': ec_refined,
            'url': f'https://www.ebi.ac.uk/intenz/query?cmd=SearchEC&ec={ec_refined}'})
        logging.debug(
            f'Replace identifiers.org to IntEnz crosslinks for EC number {ec_refined}')
    # Not EC cases
    # TODO complete me
    return xlinks


def _get_reaction_rule_score(rxn_dict):
    try:
        return round(rxn_dict['brsynth']['rule_score'], 3)
    except KeyError:
        return None


def _get_specie_node_id(specie_dict, specie_id=None):
    """Return a useful ID for the specie node.

    A compound/specie node could be shared between several pathways,
    the inchikey, MNXM ID and chebi ID are reliable way to detect
    identical compounds.
    """
    if _get_specie_inchikey(specie_dict) is not None:
        return _get_specie_inchikey(specie_dict)
    elif 'metanetx' in specie_dict['miriam'] \
            and len(specie_dict['miriam']['metanetx']):
        sorted_mnx_ids = sorted(
            specie_dict['miriam']['metanetx'],
            key=lambda x: int(x.replace('MNXM', ''))
        )
        return sorted_mnx_ids[0]
    elif 'chebi' in specie_dict['miriam'] \
            and len(specie_dict['miriam']['chebi']):
        sorted_chebi_ids = sorted(
            specie_dict['miriam']['chebi'],
            key=lambda x: int(x.replace('CHEBI:', ''))
        )
        return sorted_chebi_ids[0]
    elif DEBUG and specie_id is not None:
        logging.error('Workaround for node ID, this should be fixed')
        return specie_id
    else:
        raise NotImplementedError('Could not assign a valid id')


def _get_specie_inchikey(specie_dict):
    try:
        return specie_dict['brsynth']['inchikey']
    except KeyError:
        return None


def _get_specie_smiles(specie_dict):
    try:
        return specie_dict['brsynth']['smiles']
    except KeyError:
        return None


def _get_specie_inchi(specie_dict):
    try:
        return specie_dict['brsynth']['inchi']
    except KeyError:
        return None


def _get_specie_xlinks(specie_dict):
    _MIRIAM_TO_IDENTIFIERS = {
        'metanetx': 'metanetx.chemical/',
        'chebi': 'chebi/CHEBI:',
        'bigg': 'bigg.metabolite/',
        'hmdb': 'hmdb/',
        'kegg_c': 'kegg.compound/',
        'kegg_d': 'kegg.drug/',
        'biocyc': 'biocyc/META:',
        'seed': 'seed.compound/',
        'metacyc': 'metacyc.compound/',
        'sabiork': 'sabiork.compound/',
        'reactome': 'reactome/'
    }
    xlinks = []
    if 'miriam' in specie_dict:
        for db_name, db_id_list in specie_dict['miriam'].items():
            for db_id in db_id_list:
                # Direct link to metacyc because identifiers.org is bugged
                if db_name == 'metacyc':
                    url_str = f'https://metacyc.org/compound?id={db_id}'
                # KEGG cases
                elif db_name == 'kegg' and db_id[0] == 'C':
                    url_str = f'http://identifiers.org/{_MIRIAM_TO_IDENTIFIERS["kegg_c"]}{db_id}'
                elif db_name == 'kegg' and db_id[0] == 'D':
                    url_str = f'http://identifiers.org/{_MIRIAM_TO_IDENTIFIERS["kegg_d"]}{db_id}'
                else:
                    url_str = f'http://identifiers.org/{_MIRIAM_TO_IDENTIFIERS[db_name]}{db_id}'
                xlinks.append({
                    'db_name': db_name,
                    'entity_id': db_id,
                    'url': url_str
                })
    return xlinks


def _nodes_seem_equal(node1, node2):
    # Few basic checks
    if node1['id'] == node2['id'] \
                and node1['type'] == node2['type'] \
                and node1['label'] == node2['label'] \
                and node1['smiles'] == node2['smiles'] \
                and node1['inchi'] == node2['inchi'] \
                and node1['inchikey'] == node2['inchikey'] \
                and node1['rsmiles'] == node2['rsmiles'] \
                and node1['rule_id'] == node2['rule_id']:
            return True
    return False


def _edge_seem_equal(edge1, edge2):
    if edge1['id'] == edge2['id'] \
            and edge1['source'] == edge2['source'] \
            and edge1['target'] == edge2['target']:
        return True
    return False


def _merge_nodes(node1, node2):
    node3 = {}
    for key in node1.keys():
        if node1[key] is None:
            value = node2[key]
        elif node2[key] is None:
            value = node1[key]
        else:
            # list of strings
            if key in ['path_ids', 'rule_id', 'all_labels']:
                value = list(set(node1[key] + node2[key]))
            # important value
            elif key in ['smiles', 'inchi', 'inchikey']:

                if node1[key] != node2[key]:
                    logging.warning(f'Not the same {key} when merging nodes: '
                                    f'{node1[key]} vs {node2[key]}. '
                                    f'Keeping the first one')
            # float
            elif key == 'rule_score':  # float value
                value = max(node1[key], node2[key])
            # list of dicts
            elif key == 'xlinks':
                value = []
                done = set()
                for entry in node1[key]:
                    tag = f'{entry["db_name"]}-{entry["entity_id"]}'
                    if tag not in done:
                        value.append(entry)
                        done.add(tag)
            # backup plan
            else:
                value = node1[key]
        node3[key] = value
    return node3


def _merge_edges(edge1, edge2):
    edge3 = {}
    for key in edge1.keys():
        if key == 'path_ids':
            value = sorted(list(set(edge1[key] + edge2[key])))
        else:
            value = edge1[key]
        edge3[key] = value
    return edge3


# def parse_one_pathway(sbml_path):
def parse_one_pathway(rpsbml_dict):
    """Extract info from one rpSBML file

    :param sbml_path: str, path to file
    """
    nodes = {}
    edges = {}
    pathway = {}

    # To dict
    # rpsbml = new_rpSBML(sbml_path)
    # rpsbml_dict = rpsbml.toDict()

    # Pathway info
    # = Mandatory values
    pathway = {
        'path_id': rpsbml_dict['pathway']['brsynth']['path_id'],
        'nb_steps': len(rpsbml_dict['reactions']),
        'node_ids': [],  # To be filled later
        'edge_ids': [],  # To be filled later
        'scores': _get_pathway_scores(rpsbml_dict['pathway']),
        'thermo_dg_m_gibbs': _get_pathway_thermo(rpsbml_dict['pathway']),
        'fba_target_flux': _get_pathway_fba(rpsbml_dict['pathway'])
    }

    # Node info: reactions
    for rxn_dict in rpsbml_dict['reactions'].values():
        node = {
            'id': _get_reaction_node_id(rxn_dict),
            'path_ids': [pathway['path_id'], ],
            'type': 'reaction',
            'label': _get_reaction_labels(rxn_dict)[0],
            'all_labels': _get_reaction_labels(rxn_dict),
            'svg': None,  # FIXME could add the reaction depiction here
            'xlinks': _get_reaction_xlinks(rxn_dict),
            # Only for reaction, None for compounds
            'rsmiles': _get_reaction_smiles(rxn_dict),
            'rule_id': [rxn_dict['brsynth']['rule_id'],],
            'ec_numbers': _get_reaction_ecs(rxn_dict),
            'thermo_dg_m_gibbs': _get_reaction_thermo(rxn_dict),
            'rule_score': _get_reaction_rule_score(rxn_dict),
            # Only for compounds
            'smiles': None,
            'inchi': None,
            'inchikey': None,
            'target_chemical': None,
            'sink_chemical': None,
            'thermo_dg_m_formation': None,
            'cofactor': None,
        }
        # Collect
        if node['id'] not in nodes:
            nodes[node['id']] = node
        else:
            try:
                assert _nodes_seem_equal(node, nodes[node['id']])
            except AssertionError:
                logging.error(f'Unexpected node inequality '
                              f'between 2 nodes having ID {node["id"]}.')

    # Node info: compounds
    for specie_id, specie_dict in rpsbml_dict['species'].items():
        node = {
            'id': _get_specie_node_id(specie_dict, specie_id),
            'path_ids': [pathway['path_id'], ],
            'type': 'chemical',
            'label': _get_specie_node_id(specie_dict, specie_id),
            'all_labels': [_get_specie_node_id(specie_dict, specie_id), ],
            'svg': None,  # Will be filled later
            'xlinks': _get_specie_xlinks(specie_dict),
            # Only for reaction, None for compounds
            'rsmiles': None,
            'rule_id': None,
            'ec_numbers': None,
            'thermo_dg_m_gibbs': None,
            'rule_score': None,
            # Only for compounds
            'smiles': _get_specie_smiles(specie_dict),
            'inchi': _get_specie_inchi(specie_dict),
            'inchikey': _get_specie_inchikey(specie_dict),
            'target_chemical': _specie_is_target(specie_id),
            'sink_chemical': _specie_is_sink(specie_id),
            'thermo_dg_m_formation': None,  # FIXME
            'cofactor': None,  # FIXME
        }
        # Collect
        if node['id'] not in nodes:
            nodes[node['id']] = node
        else:
            try:
                assert _nodes_seem_equal(node, nodes[node['id']])
                # TODO merge nodes even if they looks equals
            except AssertionError:
                logging.error(f'Unexpected node inequality '
                              f'between 2 nodes having ID {node["id"]}.')

    # Edges
    for rxn_dict in rpsbml_dict['reactions'].values():
        rxn_node_id = _get_reaction_node_id(rxn_dict)
        for side in ('left', 'right'):
            for specie_id, specie_coeff in rxn_dict['brsynth'][side].items():
                specie_dict = rpsbml_dict['species'][specie_id]
                specie_node_id = _get_specie_node_id(specie_dict, specie_id)
                if side == 'left':
                    edge_id = f'{specie_node_id}_{rxn_node_id}'
                    edge = {
                        'id': edge_id,
                        'path_ids': [pathway['path_id'], ],
                        'source': specie_node_id,
                        'target': rxn_node_id
                    }
                else:
                    edge_id = f'{rxn_node_id}_{specie_node_id}'
                    edge = {
                        'id': edge_id,
                        'path_ids': [pathway['path_id'], ],
                        'source': rxn_node_id,
                        'target': specie_node_id
                    }
                if edge_id not in edges:
                    edges[edge_id] = edge
                else:
                    try:
                        assert _edge_seem_equal(edge, edges[edge_id])
                    except AssertionError:
                        logging.error(f'Unexpected edge inequality '
                                      f'between 2 edges having ID {edge_id}.')

    # Update pathway info
    pathway['node_ids'] = list(nodes.keys())
    pathway['edge_ids'] = list(edges.keys())

    return nodes, edges, pathway


def parse_all_pathways(input_files):
    network = {'elements': {'nodes': [], 'edges': []}}
    all_nodes = {}
    all_edges = {}
    pathways_info = {}

    for sbml_path in input_files:
        rpsbml = rpSBML(str(sbml_path))
        rpsbml_dict = rpsbml.toDict()
        nodes, edges, pathway = parse_one_pathway(rpsbml_dict)
        # Store pathway
        pathways_info[pathway['path_id']] = pathway
        # Store nodes
        for node_id, node_dict in nodes.items():
            if node_id in all_nodes:
                all_nodes[node_id] = _merge_nodes(node_dict, all_nodes[node_id])
            else:
                all_nodes[node_id] = node_dict
        # Store edges
        for edge_id, edge_dict in edges.items():
            if edge_id in all_edges:
                all_edges[edge_id] = _merge_edges(edge_dict, all_edges[edge_id])
            else:
                all_edges[edge_id] = edge_dict

    # Finally store nodes
    for node in all_nodes.values():
        network['elements']['nodes'].append({'data': node})
    for edge in all_edges.values():
        network['elements']['edges'].append({'data': edge})

    # Finally, sort node and edge IDs everywhere
    for node in network['elements']['nodes']:
        node['data']['path_ids'] = sorted(node['data']['path_ids'])
    for node in network['elements']['edges']:
        node['data']['path_ids'] = sorted(node['data']['path_ids'])
    # Finally, sort pathway_info by pathway ID
    pathways_info_ordered = {}
    path_ids_ordered = sorted(pathways_info.keys())
    for path_id in path_ids_ordered:
        pathways_info_ordered[path_id] = pathways_info[path_id]

    return network, pathways_info_ordered


# def sbml_to_json(input_folder, pathway_id='rp_pathway', sink_species_group_id='rp_sink_species'):
#     """Parse the collection of rpSBML files and outputs as dictionaries the network and pathway info

#     :param input_folder: str,  path to the folder containing the collection of rpSBML
#     :param pathway_id: str, pathway_ID prefix
#     :return: 2 dictionaries, network and pathways_info

#     Notice: need to parse the structure to SVG files
#     """
#     network = {'elements': {'nodes': [], 'edges': []}}
#     pathways_info = {}

#     # Shortcuts
#     reac_nodes = {}
#     chem_nodes = {}
#     edges_nodes = {}

#     # glob.escape() prevents issues with brackets in the inputted path
#     for sbml_path in glob.glob(glob.escape(input_folder) + '/*.xml'):
#         filename = sbml_path.split('/')[-1].replace('.sbml', '').replace('.rpsbml', '').replace('.xml', '')
#         rpsbml = old_rpSBML(filename)
#         rpsbml.readSBML(sbml_path)
#         groups = rpsbml.model.getPlugin('groups')
#         rp_pathway = groups.getGroup(pathway_id)
#         brsynth_annot = rpsbml.readBRSYNTHAnnotation(rp_pathway.getAnnotation())
#         norm_scores = [i for i in brsynth_annot if i[:5] == 'norm_']
#         norm_scores.append('global_score')
#         logging.info('norm_scores: ' + str(norm_scores))
#         ############## pathway_id ##############
#         scores = {}
#         pathway_rule_scores = []
#         for i in norm_scores:
#             try:
#                 scores[i] = brsynth_annot[i]['value']
#             except KeyError:
#                 logging.warning(
#                     'Cannot retrieve the following information in rpSBML: ' + str(i) + '. Setting to 0.0...')
#                 pass
#         try:
#             target_flux = brsynth_annot['fba_obj_fraction']['value']
#         except KeyError:
#             logging.warning('Cannot retrieve objective function fba_obj_fraction, must be another one')
#             target_flux = 0.0
#         pathways_info[rpsbml.modelName] = {
#             'path_id': rpsbml.modelName,
#             'node_ids': [],
#             'edge_ids': [],
#             'scores': scores,
#             'nb_steps': rp_pathway.num_members,
#             'fba_target_flux': target_flux,
#             'thermo_dg_m_gibbs': None,
#             'rule_score': None
#         }
#         try:
#             pathways_info[rpsbml.modelName]['thermo_dg_m_gibbs'] = brsynth_annot['dfG_prime_m']['value']
#         except KeyError:
#             pass
#         ################ REACTIONS #######################
#         for reaction_name in rpsbml.readRPpathwayIDs():
#             reaction = rpsbml.model.getReaction(reaction_name)
#             brsynth_annot = rpsbml.readBRSYNTHAnnotation(reaction.getAnnotation())
#             miriam_annot = rpsbml.readMIRIAMAnnotation(reaction.getAnnotation())
#             # Build the node ID -- Based on the reaction SMILES
#             tmp_smiles = None
#             if not 'smiles' in brsynth_annot:
#                 try:
#                     node_id = sorted(miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXR', '')))[0]
#                 except KeyError:
#                     try:
#                         node_id = sorted(miriam_annot['kegg'], key=lambda x: int(x.replace('R', '')))[0]
#                     except KeyError:
#                         logging.error('Could not assign a valid ID, node reaction skipped')
#                         continue
#             else:
#                 node_id = brsynth_annot['smiles']
#                 tmp_smiles = brsynth_annot['smiles']
#             # Build a new node if not met yet
#             if node_id not in reac_nodes:
#                 node = dict()
#                 node['id'] = node_id
#                 node['path_ids'] = [rpsbml.modelName]
#                 node['type'] = 'reaction'
#                 if ('ec-code' in miriam_annot) and (len(miriam_annot['ec-code'])):
#                     node['label'] = miriam_annot['ec-code'][0]  # Expected to be a list
#                     node['all_labels'] = miriam_annot['ec-code'] + [brsynth_annot['rule_id']]
#                 else:
#                     node['label'] = brsynth_annot['rule_id']
#                     node['all_labels'] = [brsynth_annot['rule_id']]
#                 node['svg'] = ''
#                 node['xlinks'] = []
#                 for xref in miriam_annot:
#                     for ref in miriam_annot[xref]:
#                         # Refine EC annotations
#                         if xref == 'ec-code':
#                             # Getting rid of dashes
#                             old_ref = ref
#                             tmp = []
#                             for _ in ref.split('.'):
#                                 if _ != '-':
#                                     tmp.append(_)
#                             ref = '.'.join(tmp)
#                             if old_ref != ref:
#                                 logging.info('Refining EC number crosslinks from {} to {}'.format(old_ref, ref))
#                             # Use direct link to workaround generic ECs issue with identifiers.org
#                             try:
#                                 node['xlinks'].append({
#                                     'db_name': 'intenz',
#                                     'entity_id': ref,
#                                     'url': 'https://www.ebi.ac.uk/intenz/query?cmd=SearchEC&ec=' + ref})
#                                 logging.debug(
#                                     'Shunting identifiers.org to IntEnz crosslinks for EC number {}'.format(ref))
#                             except KeyError:
#                                 pass
#                         # Generic case
#                         else:
#                             try:
#                                 node['xlinks'].append({
#                                     'db_name': xref,
#                                     'entity_id': ref,
#                                     'url': 'http://identifiers.org/' + miriam_header['reaction'][xref] + str(ref)})
#                             except KeyError:
#                                 pass
#                 node['rsmiles'] = tmp_smiles
#                 node['rule_id'] = brsynth_annot['rule_id']
#                 try:
#                     node['ec_numbers'] = miriam_annot['ec-code']
#                 except KeyError:
#                     node['ec_numbers'] = None
#                 try:
#                     node['thermo_dg_m_gibbs'] = brsynth_annot['dfG_prime_m']['value']
#                 except KeyError:
#                     node['thermo_dg_m_gibbs'] = None
#                 # node['fba_reaction'] = '0'
#                 try:
#                     node['rule_score'] = round(brsynth_annot['rule_score']['value'], 3)
#                     pathway_rule_scores.append(brsynth_annot['rule_score']['value'])
#                 except KeyError:
#                     node['rule_score'] = None
#                     pathway_rule_scores.append(0.0)
#                 node['smiles'] = None
#                 node['inchi'] = None
#                 node['inchikey'] = None
#                 node['target_chemical'] = None
#                 node['sink_chemical'] = None
#                 node['thermo_dg_m_formation'] = None
#                 node['cofactor'] = None
#                 # Store
#                 reac_nodes[tmp_smiles] = node
#             # Update already existing node
#             else:
#                 try:
#                     node['rule_score'] = round(brsynth_annot['rule_score']['value'], 3)
#                     pathway_rule_scores.append(brsynth_annot['rule_score']['value'])
#                 except KeyError:
#                     node['rule_score'] = None
#                     pathway_rule_scores.append(0.0)
#                 if rpsbml.modelName not in reac_nodes[node_id]['path_ids']:
#                     reac_nodes[node_id]['path_ids'].append(rpsbml.modelName)
#                 if brsynth_annot['rule_id'] not in reac_nodes[node_id]['all_labels']:
#                     reac_nodes[node_id]['all_labels'].append(brsynth_annot['rule_id'])
#                 try:
#                     assert tmp_smiles == reac_nodes[node_id]['rsmiles']
#                 except AssertionError as e:
#                     logging.warning(e)
#                 try:
#                     assert brsynth_annot['rule_id'] == reac_nodes[node_id]['rule_id']
#                 except AssertionError as e:
#                     logging.warning(e)
#             # Keep track for pathway info
#             if node_id not in pathways_info[rpsbml.modelName]['node_ids']:
#                 pathways_info[rpsbml.modelName]['node_ids'].append(node_id)
#         pathways_info[rpsbml.modelName]['rule_score'] = round(mean(pathway_rule_scores), 3)
#         ################# CHEMICALS #########################
#         ## compile all the species that are sink molecules
#         #
#         largest_rp_reac_id = \
#             sorted([i.getIdRef() for i in rp_pathway.getListOfMembers()], key=lambda x: int(x.replace('RP', '')),
#                    reverse=True)[0]
#         reactants = [i.species for i in rpsbml.model.getReaction(largest_rp_reac_id).getListOfReactants()]
#         sink_species = [i.getIdRef() for i in groups.getGroup(sink_species_group_id).getListOfMembers()]
#         '''
#         sink_molecules_inchikey = []
#         for i in reactants:
#             if i in sink_species:
#                 spec_annot = rpsbml.readBRSYNTHAnnotation(rpsbml.model.getSpecies(i).getAnnotation())
#                 if 'inchikey' in spec_annot:
#                     sink_molecules_inchikey.append(spec_annot['inchikey'])
#                 #TODO: use other keys when the species does not have an inchikey
#         '''
#         for species_name in rpsbml.readUniqueRPspecies():
#             species = rpsbml.model.getSpecies(species_name)
#             brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
#             miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
#             # Build the node ID -- Based on if available the inchikey, else on MNX crosslinks
#             if not 'inchikey' in brsynth_annot:
#                 try:
#                     node_id = sorted(miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
#                 except KeyError:
#                     try:
#                         node_id = sorted(miriam_annot['chebi'], key=lambda x: int(x.replace('CHEBI:', '')))[0]
#                     except KeyError:
#                         logging.error('Could not assign a valid id, chemical node skipped')
#                         continue
#             else:
#                 node_id = brsynth_annot['inchikey']
#             # Make a new node in the chemical has never been met yet
#             if node_id not in chem_nodes:
#                 node = dict()
#                 node['id'] = node_id
#                 node['path_ids'] = [rpsbml.modelName]
#                 node['type'] = 'chemical'
#                 node['label'] = node_id
#                 node['all_labels'] = [node_id]
#                 node['svg'] = ''
#                 node['xlinks'] = []
#                 for xref in miriam_annot:
#                     if xref == 'reactome':
#                         continue
#                     if xref == 'metacyc':
#                         continue
#                     for ref in miriam_annot[xref]:
#                         try:
#                             if not all([xref == 'bigg', len(ref.split('_')) > 1]):
#                                 # print(xref)
#                                 if xref == 'kegg' and ref[0] == 'C':
#                                     url_str = 'http://identifiers.org/' + miriam_header['species']['kegg_c'] + ref
#                                 elif xref == 'kegg' and ref[0] == 'D':
#                                     url_str = 'http://identifiers.org/' + miriam_header['species']['kegg_d'] + ref
#                                 else:
#                                     url_str = 'http://identifiers.org/' + miriam_header['species'][xref] + ref
#                                 node['xlinks'].append({
#                                     'db_name': xref,
#                                     'entity_id': ref,
#                                     'url': url_str})
#                         except KeyError:
#                             pass
#                 node['rsmiles'] = None
#                 node['rule_id'] = None
#                 node['ec_numbers'] = None
#                 node['thermo_dg_m_gibbs'] = None
#                 # node['fba_reaction'] = None
#                 node['rule_score'] = None
#                 try:
#                     node['smiles'] = brsynth_annot['smiles']
#                 except KeyError:
#                     node['smiles'] = None
#                 try:
#                     node['inchi'] = brsynth_annot['inchi']
#                 except KeyError:
#                     node['inchi'] = None
#                 try:
#                     node['inchikey'] = brsynth_annot['inchikey']
#                 except KeyError:
#                     node['inchikey'] = None
#                 # TODO: need a better way if not TARGET in name
#                 if species_name[:6] == 'TARGET':
#                     node['target_chemical'] = 1
#                 else:
#                     node['target_chemical'] = 0
#                 node['cofactor'] = 0
#                 # check the highest RP{\d} reactants and ignore cofactors
#                 # TODO: not great but most time inchikey is the key
#                 if species_name in sink_species:
#                     node['sink_chemical'] = 1
#                 else:
#                     node['sink_chemical'] = 0
#                 # Store
#                 chem_nodes[node_id] = node
#             # Else update already existing node
#             else:
#                 if rpsbml.modelName not in chem_nodes[node_id]['path_ids']:
#                     chem_nodes[node_id]['path_ids'].append(rpsbml.modelName)
#                 # TODO: manage xref, without adding duplicates
#                 try:
#                     assert brsynth_annot.get('smiles', None) == chem_nodes[node_id]['smiles']
#                 except AssertionError:
#                     try:
#                         msg = 'Not the same SMILES: {} vs. {}'.format(
#                             brsynth_annot['smiles'],
#                             chem_nodes[node_id]['smiles']
#                         )
#                         logging.warning(msg)
#                     except KeyError:
#                         logging.warning('The brsynth_annot has no smiles: ' + str(node_id))
#                         logging.info(brsynth_annot)
#                 try:
#                     assert brsynth_annot.get('inchi', None) == chem_nodes[node_id]['inchi']
#                 except AssertionError:
#                     try:
#                         msg = 'Not the same INCHI: {} vs. {}'.format(
#                             brsynth_annot['inchi'],
#                             chem_nodes[node_id]['inchi']
#                         )
#                         logging.warning(msg)
#                     except KeyError:
#                         logging.warning('The brsynth_annot has no inchi: ' + str(node_id))
#                         logging.info(brsynth_annot)
#                 try:
#                     assert brsynth_annot.get('inchikey', None) == chem_nodes[node_id]['inchikey']
#                 except AssertionError:
#                     try:
#                         msg = 'Not the same INCHIKEY: {} vs. {}'.format(
#                             brsynth_annot['inchikey'],
#                             chem_nodes[node_id]['inchikey']
#                         )
#                         logging.warning(msg)
#                     except KeyError:
#                         logging.warning('The brsynth_annot has no inchi: ' + str(node_id))
#                         logging.info(brsynth_annot)
#             # Keep track for pathway info
#             if node_id not in pathways_info[rpsbml.modelName]['node_ids']:
#                 pathways_info[rpsbml.modelName]['node_ids'].append(node_id)
#         ################### EDGES ###########################
#         for reaction_name in rpsbml.readRPpathwayIDs():
#             reaction = rpsbml.model.getReaction(reaction_name)
#             reac_species = rpsbml.readReactionSpecies(reaction)
#             reac_brsynth_annot = rpsbml.readBRSYNTHAnnotation(reaction.getAnnotation())
#             reac_miriam_annot = rpsbml.readMIRIAMAnnotation(reaction.getAnnotation())
#             # Deduce reaction ID -- TODO: make this more robust
#             if not 'smiles' in reac_brsynth_annot:
#                 try:
#                     reac_nodeid = sorted(reac_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXR', '')))[0]
#                 except KeyError:
#                     logging.warning('Could not assign valid id')
#                     continue
#             else:
#                 reac_nodeid = reac_brsynth_annot['smiles']
#             # Iterate over chemicals linked to the reaction as substrate
#             for spe in reac_species['left']:
#                 species = rpsbml.model.getSpecies(spe)
#                 spe_brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
#                 spe_miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
#                 # Deduce chemical ID -- TODO: make this more robust
#                 if not 'inchikey' in spe_brsynth_annot:
#                     try:
#                         spe_nodeid = sorted(spe_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
#                     except KeyError:
#                         logging.warning('Could not assign a valid ID, edge skipped')
#                         continue
#                 else:
#                     spe_nodeid = spe_brsynth_annot['inchikey']
#                 # Build the edge ID
#                 node_id = spe_nodeid + '_' + reac_nodeid
#                 # Build a new node if this edge has never been met yet
#                 if node_id not in edges_nodes:
#                     node = dict()
#                     node['id'] = node_id
#                     node['path_ids'] = [rpsbml.modelName]
#                     node['source'] = spe_nodeid
#                     node['target'] = reac_nodeid
#                     # Store the new node
#                     edges_nodes[node_id] = node
#                 # Else, update the already existing node
#                 else:
#                     if rpsbml.modelName not in edges_nodes[node_id]['path_ids']:
#                         edges_nodes[node_id]['path_ids'].append(rpsbml.modelName)
#                     try:
#                         assert spe_nodeid == edges_nodes[node_id]['source']
#                     except AssertionError:
#                         logging.warning('Unexpected issue met, but execution still continued')
#                     try:
#                         assert reac_nodeid == edges_nodes[node_id]['target']
#                     except AssertionError:
#                         logging.warning('Unexpected issue met, but execution still continued')
#                 # Keep track for pathway info
#                 if rpsbml.modelName not in pathways_info[rpsbml.modelName]['edge_ids']:
#                     pathways_info[rpsbml.modelName]['edge_ids'].append(node_id)
#             # Iterate over chemicals linked to the reaction as product
#             for spe in reac_species['right']:
#                 species = rpsbml.model.getSpecies(spe)
#                 spe_brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
#                 spe_miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
#                 # Deduce chemical ID -- TODO: make this more robust
#                 if not 'inchikey' in spe_brsynth_annot:
#                     try:
#                         spe_nodeid = sorted(spe_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
#                     except KeyError:
#                         logging.warning('Could not assign a valid ID, edge skipped')
#                         continue
#                 else:
#                     spe_nodeid = spe_brsynth_annot['inchikey']
#                 # Build the edge ID
#                 node_id = reac_nodeid + '_' + spe_nodeid
#                 # Build a new node if this edge has never been met yet
#                 if node_id not in edges_nodes:
#                     node = dict()
#                     node['id'] = node_id
#                     node['path_ids'] = [rpsbml.modelName]
#                     node['source'] = reac_nodeid
#                     node['target'] = spe_nodeid
#                     # Store the new node
#                     edges_nodes[node_id] = node
#                 else:
#                     if rpsbml.modelName not in edges_nodes[node_id]['path_ids']:
#                         edges_nodes[node_id]['path_ids'].append(rpsbml.modelName)
#                     try:
#                         assert reac_nodeid == edges_nodes[node_id]['source']
#                     except AssertionError:
#                         logging.warning('Unexpected issue met, but execution still continued, mark A')
#                     try:
#                         assert spe_nodeid == edges_nodes[node_id]['target']
#                     except AssertionError:
#                         logging.warning('Unexpected issue met, but execution still continued, mark B')
#                 # Keep track for pathway info
#                 if rpsbml.modelName not in pathways_info[rpsbml.modelName]['edge_ids']:
#                     pathways_info[rpsbml.modelName]['edge_ids'].append(node_id)

#     # Finally store nodes
#     for node in reac_nodes.values():
#         network['elements']['nodes'].append({'data': node})
#     for node in chem_nodes.values():
#         network['elements']['nodes'].append({'data': node})
#     for edge in edges_nodes.values():
#         network['elements']['edges'].append({'data': edge})

#     # Finally, sort node and edge IDs everywhere
#     try:
#         network_backup = network.copy()
#         for node in network['elements']['nodes']:
#             node['data']['path_ids'] = sorted(node['data']['path_ids'],
#                                               key=lambda x: [int(s) for s in x.split('_')[1:]])
#         for node in network['elements']['edges']:
#             node['data']['path_ids'] = sorted(node['data']['path_ids'],
#                                               key=lambda x: [int(s) for s in x.split('_')[1:]])
#     except ValueError:
#         logging.warning('Cannot reorder pathway IDs into node and edge items, skipped')
#         network = network_backup.copy()

#     # Finally, sort pathway_info by pathway ID
#     try:
#         pathways_info_ordered = OrderedDict()
#         path_ids_ordered = sorted(pathways_info.keys(), key=lambda x: [int(s) for s in x.split('_')[1:]])
#         for path_id in path_ids_ordered:
#             pathways_info_ordered[path_id] = pathways_info[path_id]
#     except ValueError:
#         logging.warning('Cannot reorder pathway_info according to pathway IDs, skipped.')
#         pathways_info_ordered = pathways_info

#     return network, pathways_info_ordered


def annotate_cofactors(network, cofactor_file):
    """Annotate cofactors based on structures listed in the cofactor file.

    :param network: dict, network of elements as outputted by the sbml_to_json method
    :param cofactor_file: str, file path
    :return: dict, network annotated
    """
    if not os.path.exists(cofactor_file):
        logging.error('Cofactor file not found: {}'.format(cofactor_file))
        return network
    # Collect cofactor structures
    cof_inchis = set()
    with open(cofactor_file, 'r') as ifh:
        reader = csv.reader(ifh, delimiter='\t')
        for row in reader:
            if row[0].startswith('#'):  # Skip comments
                continue
            try:
                assert row[0].startswith('InChI')
            except AssertionError:
                msg = 'Cofactor skipped, depiction is not a valid InChI for row: {}'.format(row)
                logging.info(msg)
                continue  # Skip row
            cof_inchis.add(row[0])
    # Match and annotate network elements
    for node in network['elements']['nodes']:
        if node['data']['type'] == 'chemical' and node['data']['inchi'] is not None:
            match = False
            for cof_inchi in cof_inchis:
                if node['data']['inchi'].find(cof_inchi) > -1:  # Match
                    node['data']['cofactor'] = 1
                    match = True
                    continue
            if match:
                continue  # Optimisation

    return network


def annotate_chemical_svg(network):
    """Annotate chemical nodes with SVGs depiction.

    :param network: dict, network of elements as outputted by the sbml_to_json method
    :return: dict, network annotated
    """
    from rdkit.Chem import MolFromInchi
    from rdkit.Chem.Draw import rdMolDraw2D
    from rdkit.Chem.AllChem import Compute2DCoords
    from urllib import parse

    for node in network['elements']['nodes']:
        if node['data']['type'] == 'chemical' and node['data']['inchi'] is not None:
            inchi = node['data']['inchi']
            try:
                mol = MolFromInchi(inchi)
                # if mol is None:
                #     raise BaseException('Mol is None')
                Compute2DCoords(mol)
                drawer = rdMolDraw2D.MolDraw2DSVG(200, 200)
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                svg_draft = drawer.GetDrawingText().replace("svg:", "")
                svg = 'data:image/svg+xml;charset=utf-8,' + parse.quote(svg_draft)
                node['data']['svg'] = svg
            except BaseException as e:
                msg = 'SVG depiction failed from inchi: "{}"'.format(inchi)
                logging.warning(msg)
                logging.warning("Below the RDKit backtrace...")
                logging.warning(e)
                node['data']['svg'] = None

    return network


def get_autonomous_html(ifolder):
    """Merge all needed file into a single HTML
    
    :param ifolder: folder containing the files to be merged
    :return html_str: string, the HTML
    """
    # find and open the index file 
    htmlString = open(ifolder + '/index.html', 'rb').read()
    # open and read JS files and replace them in the HTML
    jsReplace = [
        'js/chroma-2.1.0.min.js',
        'js/cytoscape-3.12.1.min.js',
        'js/cytoscape-dagre-2.2.1.js',
        'js/dagre-0.8.5.min.js',
        'js/jquery-3.4.1.min.js',
        'js/jquery-ui-1.12.1.min.js',
        'js/jquery.tablesorter-2.31.2.min.js',
        'js/viewer.js'
    ]
    for js in jsReplace:
        jsString = open(ifolder + '/' + js, 'rb').read()
        ori = b'src="' + js.encode() + b'">'
        rep = b'>' + jsString
        htmlString = htmlString.replace(ori, rep)
    # open and read style.css and replace it in the HTML
    cssReplace = ['css/jquery.tablesorte.theme.default-2.31.2.min.css',
                  'css/viewer.css']
    for css_file in cssReplace:
        cssBytes = open(ifolder + '/' + css_file, 'rb').read()
        ori = b'<link href="' + css_file.encode() + b'" rel="stylesheet" type="text/css"/>'
        rep = b'<style type="text/css">' + cssBytes + b'</style>'
        htmlString = htmlString.replace(ori, rep)
    ### replace the network
    netString = open(ifolder + '/network.json', 'rb').read()
    ori = b'src="' + 'network.json'.encode() + b'">'
    rep = b'>' + netString
    htmlString = htmlString.replace(ori, rep)
    return htmlString


if __name__ == '__main__':
    pass
