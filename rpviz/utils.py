# -*- coding: utf-8 -*-
"""
Created on Thu Now 7 2019

@author: Thomas

"""


import os
import csv
import glob
import logging

from collections import OrderedDict

from rpviz import rpSBML


def sbml_to_json(input_folder, pathway_id='rp_pathway'):
    """Parse the collection of rpSBML files and outputs as dictionaries the network and pathway info

    :param input_folder: str,  path to the folder containing the collection of rpSBML
    :param pathway_id: str, pathway_ID prefix
    :return: 2 dictionaries, network and pathways_info

    Notice: need to parse the structure to SVG files
    """
    network = {'elements': {'nodes': [], 'edges': []}}
    pathways_info = {}

    # Shortcuts
    reac_nodes = {}
    chem_nodes = {}
    edges_nodes = {}

    # glob.escape() prevents issues with brackets in the inputted path
    for sbml_path in glob.glob(glob.escape(input_folder) + '/*.xml'):
        filename = sbml_path.split('/')[-1].replace('.sbml.xml', '')
        rpsbml = rpSBML.rpSBML(filename)
        rpsbml.readSBML(sbml_path)
        ############## pathway_id ##############
        pathways_info[rpsbml.modelName] = {
            'path_id': rpsbml.modelName,
            'node_ids': [],
            'edge_ids': [],
            'scores': {}
        }
        groups = rpsbml.model.getPlugin('groups')
        rp_pathway = groups.getGroup(pathway_id)
        try:
            pathways_info[rpsbml.modelName]['scores']['globalScore'] = rp_pathway.getAnnotation()\
                .getChild('RDF').getChild('BRSynth').getChild('brsynth').getChild('global_score')\
                .getAttrValue(0)
        except ValueError:
            logging.warning('Could not extract pathway score')
        ################ REACTIONS #######################
        for reaction_name in rpsbml.readRPpathwayIDs():
            reaction = rpsbml.model.getReaction(reaction_name)
            brsynth_annot = rpsbml.readBRSYNTHAnnotation(reaction.getAnnotation())
            miriam_annot = rpsbml.readMIRIAMAnnotation(reaction.getAnnotation())
            # Build the node ID -- Based on the reaction SMILES
            if brsynth_annot['smiles'] == '' or brsynth_annot['smiles'] is None:
                try:
                    node_id = sorted(miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXR', '')))[0]
                except KeyError:
                    logging.error('Could not assign a valid ID, node reaction skipped')
                    continue
            else:
                node_id = brsynth_annot['smiles']
            # Build a new node if not met yet
            if node_id not in reac_nodes:
                node = dict()
                node['id'] = node_id
                node['path_ids'] = [rpsbml.modelName]
                node['type'] = 'reaction'
                node['label'] = brsynth_annot['rule_id']
                node['all_labels'] = [brsynth_annot['rule_id']]
                node['svg'] = ''
                node['xlinks'] = []
                for xref in miriam_annot:
                    for ref in miriam_annot[xref]:
                        node['xlinks'].append({
                            'db_name': xref,
                            'entity_id': ref,
                            'url': 'http://identifiers.org/'+xref+'/'+ref
                        })
                node['rsmiles'] = brsynth_annot['smiles']
                node['rule_id'] = brsynth_annot['rule_id']
                node['fba_reaction'] = '0'
                node['smiles'] = None
                node['inchi'] = None
                node['inchikey'] = None
                node['target_chemical'] = None
                node['cofactor'] = None
                # Store
                reac_nodes[brsynth_annot['smiles']] = node
            # Update already existing node
            else:
                if rpsbml.modelName not in reac_nodes[node_id]['path_ids']:
                    reac_nodes[node_id]['path_ids'].append(rpsbml.modelName)
                if brsynth_annot['rule_id'] not in reac_nodes[node_id]['all_labels']:
                    reac_nodes[node_id]['all_labels'].append(brsynth_annot['rule_id'])
                # TODO: manage xref, without adding duplicates
                try:
                    assert brsynth_annot['smiles'] == reac_nodes[node_id]['rsmiles']
                except AssertionError as e:
                    logging.error(e)
                try:
                    assert brsynth_annot['rule_id'] == reac_nodes[node_id]['rule_id']
                except AssertionError as e:
                    logging.error(e)
                try:
                    assert brsynth_annot['smiles'] == reac_nodes[node_id]['rsmiles']
                except AssertionError as e:
                    logging.error(e)
            # Keep track for pathway info
            if node_id not in pathways_info[rpsbml.modelName]['node_ids']:
                pathways_info[rpsbml.modelName]['node_ids'].append(node_id)
        ################# CHEMICALS #########################
        for species_name in rpsbml.readUniqueRPspecies():
            species = rpsbml.model.getSpecies(species_name)
            brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
            miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
            # Build the node ID -- Based on if available the inchikey, else on MNX crosslinks
            if brsynth_annot['inchikey'] == '' or brsynth_annot['inchikey'] is None:
                try:
                    node_id = sorted(miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
                except KeyError:
                    logging.error('Could not assign a valid id, chemical node skipped')
                    continue
            else:
                node_id = brsynth_annot['inchikey']
            # Make a new node in the chemical has never been met yet
            if node_id not in chem_nodes:
                node = dict()
                node['id'] = node_id
                node['path_ids'] = [rpsbml.modelName]
                node['type'] = 'chemical'
                node['label'] = node_id
                node['all_labels'] = [node_id]
                node['svg'] = ''
                node['xlinks'] = []
                for xref in miriam_annot:
                    for ref in miriam_annot[xref]:
                        node['xlinks'].append({
                            'db_name': xref,
                            'entity_id': ref,
                            'url': 'http://identifiers.org/' + xref + '/' + ref
                        })
                node['rsmiles'] = None
                node['rule_id'] = None
                node['fba_reaction'] = None
                node['smiles'] = brsynth_annot['smiles']
                node['inchi'] = brsynth_annot['inchi']
                node['inchikey'] = brsynth_annot['inchikey']
                if species_name[:6] == 'TARGET':  # TODO: keep this in mind
                    node['target_chemical'] = 1
                else:
                    node['target_chemical'] = 0
                node['cofactor'] = 0
                # Store
                chem_nodes[node_id] = node
            # Else update already existing node
            else:
                if rpsbml.modelName not in chem_nodes[node_id]['path_ids']:
                    chem_nodes[node_id]['path_ids'].append(rpsbml.modelName)
                # TODO: manage xref, without adding duplicates
                try:
                    assert brsynth_annot['smiles'] == chem_nodes[node_id]['smiles']
                except AssertionError:
                    msg = 'Not the same SMILES: {} vs. {}'.format(
                        brsynth_annot['smiles'],
                        chem_nodes[node_id]['smiles']
                    )
                    logging.error(msg)
                try:
                    assert brsynth_annot['inchi'] == chem_nodes[node_id]['inchi']
                except AssertionError:
                    msg = 'Not the same INCHI: {} vs. {}'.format(
                        brsynth_annot['inchi'],
                        chem_nodes[node_id]['inchi']
                    )
                    logging.error(msg)
                try:
                    assert brsynth_annot['inchikey'] == chem_nodes[node_id]['inchikey']
                except AssertionError:
                    msg = 'Not the same INCHIKEY: {} vs. {}'.format(
                        brsynth_annot['inchikey'],
                        chem_nodes[node_id]['inchikey']
                    )
                    logging.error(msg)
            # Keep track for pathway info
            if node_id not in pathways_info[rpsbml.modelName]['node_ids']:
                pathways_info[rpsbml.modelName]['node_ids'].append(node_id)
        ################### EDGES ###########################
        for reaction_name in rpsbml.readRPpathwayIDs():
            reaction = rpsbml.model.getReaction(reaction_name)
            reac_species = rpsbml.readReactionSpecies(reaction)
            reac_brsynth_annot = rpsbml.readBRSYNTHAnnotation(reaction.getAnnotation())
            reac_miriam_annot = rpsbml.readMIRIAMAnnotation(reaction.getAnnotation())
            # Deduce reaction ID -- TODO: make this more robust
            if reac_brsynth_annot['smiles'] == '' or reac_brsynth_annot['smiles'] is None:
                try:
                    reac_nodeid = sorted(reac_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXR', '')))[0]
                except KeyError:
                    logging.error('Could not assign valid id')
                    continue
            else:
                reac_nodeid = reac_brsynth_annot['smiles']
            # Iterate over chemicals linked to the reaction as substrate
            for spe in reac_species['left']:
                species = rpsbml.model.getSpecies(spe)
                spe_brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
                spe_miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
                # Deduce chemical ID -- TODO: make this more robust
                if spe_brsynth_annot['inchikey'] == '' or spe_brsynth_annot['inchikey'] is None:
                    try:
                        spe_nodeid = sorted(spe_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
                    except KeyError:
                        logging.error('Could not assign a valid ID, edge skipped')
                        continue
                else:
                    spe_nodeid = spe_brsynth_annot['inchikey']
                # Build the edge ID
                node_id = spe_nodeid + '_' + reac_nodeid
                # Build a new node if this edge has never been met yet
                if node_id not in edges_nodes:
                    node = dict()
                    node['id'] = node_id
                    node['path_ids'] = [rpsbml.modelName]
                    node['source'] = spe_nodeid
                    node['target'] = reac_nodeid
                    # Store the new node
                    edges_nodes[node_id] = node
                # Else, update the already existing node
                else:
                    if rpsbml.modelName not in edges_nodes[node_id]['path_ids']:
                        edges_nodes[node_id]['path_ids'].append(rpsbml.modelName)
                    try:
                        assert spe_nodeid == edges_nodes[node_id]['source']
                    except AssertionError:
                        logging.error('Unexpected error met, but execution still continued')
                    try:
                        assert reac_nodeid == edges_nodes[node_id]['target']
                    except AssertionError:
                        logging.error('Unexpected error met, but execution still continued')
                # Keep track for pathway info
                if rpsbml.modelName not in pathways_info[rpsbml.modelName]['edge_ids']:
                    pathways_info[rpsbml.modelName]['edge_ids'].append(node_id)
            # Iterate over chemicals linked to the reaction as product
            for spe in reac_species['right']:
                species = rpsbml.model.getSpecies(spe)
                spe_brsynth_annot = rpsbml.readBRSYNTHAnnotation(species.getAnnotation())
                spe_miriam_annot = rpsbml.readMIRIAMAnnotation(species.getAnnotation())
                # Deduce chemical ID -- TODO: make this more robust
                if spe_brsynth_annot['inchikey'] == '' or spe_brsynth_annot['inchikey'] is None:
                    try:
                        spe_nodeid = sorted(spe_miriam_annot['metanetx'], key=lambda x: int(x.replace('MNXM', '')))[0]
                    except KeyError:
                        logging.error('Could not assign a valid ID, edge skipped')
                        continue
                else:
                    spe_nodeid = spe_brsynth_annot['inchikey']
                # Build the edge ID
                node_id = reac_nodeid + '_' + spe_nodeid
                # Build a new node if this edge has never been met yet
                if node_id not in edges_nodes:
                    node = dict()
                    node['id'] = node_id
                    node['path_ids'] = [rpsbml.modelName]
                    node['source'] = reac_nodeid
                    node['target'] = spe_nodeid
                    # Store the new node
                    edges_nodes[node_id] = node
                else:
                    if rpsbml.modelName not in edges_nodes[node_id]['path_ids']:
                        edges_nodes[node_id]['path_ids'].append(rpsbml.modelName)
                    try:
                        assert reac_nodeid == edges_nodes[node_id]['source']
                    except AssertionError:
                        logging.error('Unexpected error met, but execution still continued, mark A')
                    try:
                        assert spe_nodeid == edges_nodes[node_id]['target']
                    except AssertionError:
                        logging.error('Unexpected error met, but execution still continued, mark B')
                # Keep track for pathway info
                if rpsbml.modelName not in pathways_info[rpsbml.modelName]['edge_ids']:
                    pathways_info[rpsbml.modelName]['edge_ids'].append(node_id)

    # Finally store nodes
    for node in reac_nodes.values():
        network['elements']['nodes'].append({'data': node})
    for node in chem_nodes.values():
        network['elements']['nodes'].append({'data': node})
    for edge in edges_nodes.values():
        network['elements']['edges'].append({'data': edge})

    # Finally, sort path IDs everywhere
    for node in network['elements']['nodes']:
        node['data']['path_ids'] = sorted(node['data']['path_ids'], key=lambda x: [int(s) for s in x.split('_')[1:]])
    for node in network['elements']['edges']:
        node['data']['path_ids'] = sorted(node['data']['path_ids'], key=lambda x: [int(s) for s in x.split('_')[1:]])

    # Finally, sort pathway_info by pathway ID
    try:
        pathways_info_ordered = OrderedDict()
        path_ids_ordered = sorted(pathways_info.keys(), key=lambda x: [int(s) for s in x.split('_')[1:]])
        for path_id in path_ids_ordered:
            pathways_info_ordered[path_id] = pathways_info[path_id]
    except Exception:
        logging.warning('Cannot reorder pathway_info according to pathway IDs.')
        pathways_info_ordered = pathways_info

    return network, pathways_info_ordered


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
                print(inchi)
                mol = MolFromInchi(inchi)
                if mol is None:
                    raise BaseException('Mol is None')
                Compute2DCoords(mol)
                drawer = rdMolDraw2D.MolDraw2DSVG(200, 200)
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                svg_draft = drawer.GetDrawingText().replace("svg:", "")
                svg = 'data:image/svg+xml;charset=utf-8,' + parse.quote(svg_draft)
                node['data']['svg'] = svg
            except BaseException as e:
                msg = 'SVG depiction failed from inchi: {}'.format(inchi)
                logging.warning(msg)
                logging.warning(e)
                node['data']['svg'] = None

    return network


if __name__ == '__main__':

    pass
