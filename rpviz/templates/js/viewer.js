/*jshint esversion: 6 */

//__author__: Thomas Duigou (thomas.duigou@inra.fr)
//__date__: 2019.12.09
//__license : MIT
//__note__ : based on Scope Viewer and Annaelle Baudier's work


class PathwayHandler {

    /**
     * 
     * @param {cytoscape.js object} cy
     * @param {json structure} pathways_info 
     */
    constructor(cy, pathways_info){
        // List of the class attributes
        this.cy = cy;
        this.all_path_ids = new Set()
        this.path_to_edges = new Object()
        this.path_to_nodes = new Object()
        this.pinned_path_ids = new Set()
        this.pinned_edge_ids = new Set()  // DEBUG: Should not be used
        this.pinned_node_ids = new Set()  // DEBUG: Should not be used
        
        for (let path_id in pathways_info){
            if (this.all_path_ids.has(path_id)){
                console.log('path_id already referenced: ' + path_id);
            } else {
                // Path ID itselft
                this.all_path_ids.add(path_id);
                // List involved edges and nodes
                info = pathways_info[path_id];
                this.path_to_edges[path_id] = info['edge_ids'];
                this.path_to_nodes[path_id] = info['node_ids'];
            }
        }
    }

    /**
     * Append path IDs to be pinned
     * 
     * @param {Array} path_ids 
     */
    add_pinned_paths(path_ids){
        for (let i = 0; i < path_ids.length;  i++){
            // Update path ids
            this.pinned_path_ids.add(path_ids[i]);
            // Update edge ids
            path_ids.forEach((path_id) => {
                let edge_ids = this.path_to_edges[path_id];
                edge_ids.forEach((edge_id) => {
                    this.pinned_edge_ids.add(edge_id);
                }, this);
            }, this);
            // Update node ids
            path_ids.forEach((path_id) => {
                let node_ids = this.path_to_nodes[path_id];
                node_ids.forEach((node_id) => {
                    this.pinned_node_ids.add(node_id);
                });
            }, this);
        }
        return
    }

    /**
     * Remove path IDs to be pinned
     * 
     * @param {Array} path_ids 
     */
    remove_pinned_paths(path_ids){
        path_ids.forEach((path_id) => {
            this.pinned_path_ids.delete(path_id);
        }, this);
    }

    /**
     * Get the list of pinned pathways
     */
    get_pinned_paths(){
        return [...this.pinned_path_ids];
    }

    /**
     * Update the visibility of pinned pathways
     */
    update_pinned_paths_visibility(){
        if (this.pinned_path_ids.size == 0){
            // "Highlight" everything if nothing is pinned
            this.cy.elements('.faded').removeClass('faded');
        } else {
            // Collect elements to highlight
            let elements_to_highlight = new Set();
            this.pinned_path_ids.forEach((path_id) => {
                let edge_ids = this.path_to_edges[path_id];
                edge_ids.forEach((edge_id) => {
                    elements_to_highlight.add(edge_id)
                });
                let node_ids = this.path_to_nodes[path_id];
                node_ids.forEach((node_id) => {
                    elements_to_highlight.add(node_id);
                });
            }, this);
            // Fade in / out elements
            this.cy.elements().forEach((element) => {
                if (elements_to_highlight.has(element.id())){
                    element.removeClass('faded');
                } else {
                    element.addClass('faded');
                }
            });
        }
        return
    }

    /**
     * Highlight "even more" a particular set of pathways
     * 
     * @param {Array} path_ids
     */
    highlight_pathways(path_ids=[]){
        if (path_ids.length == 0){
            this.cy.elements('.highlighted').removeClass('highlighted');
        } else {
            // Collect
            let edges_to_highlight = new Set();
            let nodes_to_highlight = new Set();
            path_ids.forEach((path_id) => {
                let edge_ids = this.path_to_edges[path_id];
                edge_ids.forEach((edge_id) => {
                    edges_to_highlight.add(edge_id)
                });
                let node_ids = this.path_to_nodes[path_id];
                node_ids.forEach((node_id) => {
                    nodes_to_highlight.add(node_id)
                });
            }, this);
            // Clean
            if (this.pinned_path_ids.size == 0){
                this.cy.elements().addClass('faded');
            }
            // Highlight
            nodes_to_highlight.forEach((element_id) => {
                let element = this.cy.getElementById(element_id);
                element.removeClass('faded');
            }, this);
            edges_to_highlight.forEach((element_id) => {
                let element = this.cy.getElementById(element_id);
                element.removeClass('faded');
                element.addClass('highlighted');
            }, this);
        }
    }
};

// Utils ///////////////////////////

/**
 * Build the pathway table
 *
 * Derived from: http://jsfiddle.net/manishmmulani/7MRx6
 */
function build_pathway_table(){
    console.assert(pathways_info);
    
    // Table skeleton
    let table_base = $('<table></table>');
    
    // Build the header
    let field_names = ['Pathway', 'Show', 'Info', 'Colour', 'Value'];
    let field_classes = ['path_id_head', 'path_checkbox_head', 'path_info_head', 'path_colour_head', 'path_value_head'];  // This is needed for tablesort
    let table_row = $('<tr></tr>');
    for (let i = 0; i < field_names.length; i++){
        let value = field_names[i];
        let class_ = field_classes[i];
        table_row.append($('<th class="' + class_ + '"></th>').html(value));
    }
    table_base.append($('<thead></thead>').append(table_row));
    
    // Build the body
    let table_body = $('<tbody></tbody>');
    for (let path_id in pathways_info){
        let info = pathways_info[path_id];
        let table_row = $('<tr></tr>');
        table_row.append($('<td class="path_id" data-path_id="' + path_id + '"></td>').html(path_id));
        table_row.append($('<td class="path_checkbox"></td>').append($('<input type="checkbox" name="path_checkbox" value=' + path_id + '>')));
        table_row.append($('<td class="path_info" data-path_id="' + path_id + '"></td>'));
        table_row.append($('<td class="path_colour" data-path_id="' + path_id + '"><input type="color" name="head" value="#A9A9A9"></td>'));
        table_row.append($('<td class="path_value" data-path_id="' + path_id + '"></td>'));
        table_body.append(table_row);
    }
    table_base.append(table_body);

    // Append the content to the HTML
    $("#table_choice").append(table_base);
    
}

/**
 *
 * Colourise pathways
 *
 * @param score_label (str): the score label to use within the path info
 */
function colourise_pathways(score_label='global_score'){
    let score_values = [];
    // Collect valid scores
    for (let path_id in pathways_info){
        let score = pathways_info[path_id]['scores'][score_label];
        if (! isNaN(score)){
            let score_value = parseFloat(score);
            score_values.push(score_value);
        }
    }
    // Set up scale
    let min_score = Math.min(...score_values);
    let max_score = Math.max(...score_values);
    let colour_maker = chroma.scale(['blue', 'red']).domain([min_score, max_score]);
    // Colourise
    for (let path_id in pathways_info){
        let score = pathways_info[path_id]['scores'][score_label];
        if (! isNaN(score)){
            // Get the score
            let score_value = parseFloat(score);
            let score_hex = colour_maker(score_value).hex();
            // Colourise the associated edges
            let edges = get_edges_from_path_id(path_id, cy);
            edges.style({
                'line-color': score_hex,
                'target-arrow-color': score_hex
            });
            // Colourise the associated color picker
            let colour_input = $('td.path_colour[data-path_id=' + path_id + '] > input')
            colour_input.val(score_hex);
        }
    }
}

/**
 * Collect checked pathways
 */
function get_checked_pathways(){
    let selected_paths=[];
    $('input[name=path_checkbox]:checked').each(function(){
        let path_id = $(this).val();
        selected_paths.push(path_id);
    });
    return selected_paths;
}

/**
 * Get the collection of edges involved in a given path_id
 *
 * @param path_id (str): pathway ID
 * @param cy (cytoscape object): Cytoscape object
 */
function get_edges_from_path_id(path_id, cy){
    edges_col = cy.collection();
    cy.edges().forEach(function(edge, index){
        let edge_path_ids = edge.data('path_ids');
        if (share_at_least_one(edge_path_ids, [path_id])){
            edges_col = edges_col.union(edge);
        }
    });
    return edges_col;
}

/**
 * Get pinned pathways IDs
 */
function get_pinned_pathway_IDs(){
    let pinned_paths = [];
    $('td.pinned').each(function(){
        let path_id = $(this).text();
        pinned_paths.push(path_id);
    });
    return pinned_paths
}

    /**
     * Put chemical info into the information panel
     */
    function panel_chemical_info(node, show=false){
        if (show){
            // Collect
            let node_id = node.data('id');
            let svg = node.data('svg');
            let smiles = node.data('smiles');
            let inchi = node.data('inchi');
            let inchikey = node.data('inchikey');
            if (node.data('cofactor') == 1){
                var cofactor = 'True';
            } else {
                var cofactor = 'False';
            }
            let xlinks = node.data('xlinks');
            let path_ids = node.data('path_ids');
            // Inject
            if (inchikey == ""){
                $("span.chem_info_inchikey").html("NA");
                $("span.chem_info_inchikey_search").html("");
            } else {
                $("span.chem_info_inchikey").html(inchikey);
                $("span.chem_info_inchikey_search").html('<a target="_blank" href="http://www.google.com/search?q=' + encodeURI(inchikey) + '">Look for identical structure using Google</a>');
            }
            if (inchi == ""){
                $("span.chem_info_inchi").html("NA");
                $("span.chem_info_inchi_search").html("");
            } else {
                $("span.chem_info_inchi").html(inchi);
                $("span.chem_info_inchi_search").html('<a target="_blank" href="https://pubchem.ncbi.nlm.nih.gov/search/#collection=compounds&query_type=structure&query_subtype=identity&query=' + encodeURI(inchi) + '">Look for identical structure using PubChem</a>');
            }
            if (smiles == ""){
                $("span.chem_info_smiles").html("NA");
                $("span.chem_info_smiles_search").html("");
            } else {
                $("span.chem_info_smiles").html(smiles);
                $("span.chem_info_smiles_search").html('<a target="_blank" href="https://pubchem.ncbi.nlm.nih.gov/search/#collection=compounds&query_type=structure&query_subtype=identity&query=' + encodeURI(smiles) + '">Look for identical structure using PubChem</a>');
            }
            $("span.chem_info_iscofactor").html(cofactor);
            // Inject SVG depiction as a background image (if any)
            if (svg !== null){
                $('div.img-box').show();
                $('div.chem_info_svg').css('background-image', "url('" + svg + "')");
            } else {
                $('div.img-box').hide();
            }
            // Inject crosslinks
            $("div.chem_info_xlinks").html('');  // Reset div content
            if (xlinks.length > 0){
                for (let i = 0; i < xlinks.length; i++){
                    $("div.chem_info_xlinks").append('<a target="_blank" href="' + xlinks[i]['url'] + '">' + xlinks[i]['db_name'] + ':' + xlinks[i]['entity_id'] + '</a>');
                    $("div.chem_info_xlinks").append('<br/>');
                }
            } else {
                $("div.chem_info_xlinks").append('None<br/>');
            }
            // Inject path IDs
            $("div.chem_info_pathids").html('');  // Reset div content
            if (path_ids.length > 0){
                for (let i = 0; i < path_ids.length; i++){
                    $("div.chem_info_pathids").append(path_ids[i] + '<br/>');
                }
            } else {
                $("div.chem_info_pathids").append('None<br/>');
            }
            // Show
            $("#panel_chemical_info").show();
        } else {
            $("#panel_chemical_info").hide();
        }
    }
    
/**
 * Put reaction info into the information panel
 */
function panel_reaction_info(node, show=true){
    if (show){
        // Collect
        let node_id = node.data('id');
        let rsmiles = node.data('rsmiles');
        let rule_id = node.data('rule_id');  // TODO: handle list of rule IDs
        let path_ids = node.data('path_ids');
        let thermo_value = node.data('thermo_dg_m_gibbs');
        // Inject
        $("span.reaction_info_rsmiles").html(rsmiles);
        $("div.reaction_info_ruleid").html(rule_id);
        // Inject path IDs
        $("div.reaction_info_pathids").html('');  // Reset div content
        if (path_ids.length > 0){
            for (let i = 0; i < path_ids.length; i++){
                $("div.reaction_info_pathids").append(path_ids[i] + '<br/>');
            }
        } else {
            $("div.reaction_info_pathids").append('None<br/>');
        }
        // Thermodynamic value
        if (isNaN(thermo_value)){
            thermo_value = "NaN";
        } else {
            thermo_value = parseFloat(thermo_value).toFixed(3);
        }
        $("span.reaction_info_thermo").html(thermo_value);
        // Selenzyme crosslink
        $("span.reaction_info_selenzyme_crosslink").html('<a target="_blank" href="http://selenzyme.synbiochem.co.uk/results?smarts=' + encodeURIComponent( rsmiles ) + '">Crosslink to Selenzyme</a>');
        // Show
        $("#panel_reaction_info").show();
    } else {
        $("#panel_reaction_info").hide();
    }
}

/**
 * Write some default text message on the info panel
 */
function panel_startup_info(show=true){  // node
    if (show){
        $("#panel_startup_legend").show();
    } else {
        $("#panel_startup_legend").hide();
    }
    
}

/**
 * Put pathway info into the information panel
 *
 * @param path_id (str): pathway ID
 */
function panel_pathway_info(path_id, show=true){
    if (show){
        // Collect
        let global_score = pathways_info[path_id]['scores']['global_score'];
        let thermo_value = pathways_info[path_id]['thermo_dg_m_gibbs'];
        let fba_value = pathways_info[path_id]['fba_target_flux'];
        let nb_steps = pathways_info[path_id]['nb_steps'];
        // Refine the global score value
        if (isNaN(global_score)){
            global_score = "NaN";
        } else {
            global_score = parseFloat(global_score).toFixed(3);
        }
        // Refines thermodynamic value
        if (isNaN(thermo_value)){
            thermo_value = "NaN";
        } else {
            thermo_value = parseFloat(thermo_value).toFixed(3);
        }
        // Refines target's flux production
        if (isNaN(fba_value)){
            fba_value = "NaN";
        } else {
            fba_value = parseFloat(fba_value).toFixed(3);
        }
        // Inject
        $("span.pathway_info_path_id").html(path_id);
        $("span.pathway_info_global_score").html(global_score);
        $("span.pathway_info_thermo").html(thermo_value);
        $("span.pathway_info_target_flux").html(fba_value);
        $("span.pathway_info_nb_steps").html(nb_steps);
        // Show
        $("#panel_pathway_info").show();
    } else {
        $("#panel_pathway_info").hide();
    }
}

/**
 * Return true if the array have at least one common items
 *
 * @param array1 (array): items
 * @param array2 (array): items
 */
function share_at_least_one(array1, array2){
    for (let i = 0; i < array1.length; i++){
        for (let j = 0; j < array2.length; j++){
            // We have  a match
            if (array1[i] == array2[j]){
                return true;
            }
        }
    }
    return false;
}

/**
 * Make labels for chemicals
 *
 * @param max_length (int): string size cutoff before label truncation
 */
function make_chemical_labels(max_length=6)
{
    let nodes = cy.nodes().filter('[type = "chemical"]');
    for (let i = 0; i < nodes.size(); i++){
        let node = nodes[i];
        let label = node.data('label');
        if ((typeof label != 'undefined') && (label != 'None') && (label != '')){
            if (label.length > max_length){
                short_label = label.substr(0, max_length-2)+'..';
            } else {
                short_label = label;
            }
        } else {
            short_label = '';
        }
        node.data('short_label', short_label);
    }
}

/**
 * Make labels for reactions
 *
 * @param max_length (int): string size cutoff before label truncation
 */
function make_reaction_labels(max_length=10)
{
    let nodes = cy.nodes().filter('[type = "reaction"]');
    for (let i = 0; i < nodes.size(); i++){
        let node = nodes[i];
        let label = node.data('label');
        if ((typeof label != 'undefined') && (label != 'None') && (label != '')){
            if (label.length > max_length){
                short_label = label.substr(0, max_length-2)+'..';
            } else {
                short_label = label;
            }
        } else {
            short_label = '';
        }
        node.data('short_label', short_label);
    }
}

// Live ///////////////////////////


$(function(){

    // Cytoscape object to play with all along
    var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),
        motionBlur: true
    });

    // Basic stuff to do only once
    build_pathway_table();
    panel_startup_info(true);
    panel_chemical_info(null, false);
    panel_reaction_info(null, false);
    panel_pathway_info(null, false);
    init_network(true);
    render_layout();
    put_pathway_values('global_score');
    make_pathway_table_sortable();  // Should be called only after the table has been populated with values
    colourise_pathways('global_score');

    // Pathway Handler stuff
    window.path_handler = new PathwayHandler(cy, pathways_info);
    
    // Extract some useful collection
    cofactor_collection = cy.elements('node[cofactor = 1]');
    cofactor_collection.merge(cofactor_collection.connectedEdges());
    
    show_cofactors(false);
    
    /**
     * Initialise the network, but hide everything
     *
     * @param show_graph (bool): show the loaded network
     */
    function init_network(show_graph=true){
        // Reset the graph
        cy.json({elements: {}});
        cy.minZoom(1e-50);
        
        // Load the full network
        cy.json({elements: network['elements']});
        
        // Create node labels
        make_chemical_labels(6);
        make_reaction_labels(10);
        
        // Hide them 'by default'
        if (! show_graph){
            show_pathways(selected_paths='__NONE__');
        } else {
            $('input[name=path_checkbox]').prop('checked', true);  // Check all
        }
        
        // Once the layout is done:
        // * set the min zoom level
        // * put default info
        cy.on('layoutstop', function(e){
            cy.minZoom(cy.zoom());
        });
        
        cy.style(
            cytoscape.stylesheet()
                .selector("node[type='reaction']")
                    .css({
                        'height': 60,
                        'width': 120,
                        'background-color': 'white',
                        'border-width': 5,
                        'border-color': 'darkgray',
                        'border-style': 'solid',
                        'content': 'data(short_label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'text-opacity': 1,
                        'color': '#575757',
                        'font-size': '20px',
                    })
                .selector("node[type='chemical']")
                    .css({
                        'background-color': '#52be80',
                        'background-fit':'contain',
                        'shape': 'roundrectangle',
                        'width': 80,
                        'height': 80,
                        'label': 'data(short_label)',
                        'font-size': '20px',
                        // 'font-weight': 'bold',
                        'text-valign': 'top',
                        'text-halign': 'center',
                        'text-margin-y': 8,
                        'text-opacity': 1,
                        'text-background-color': 'White',
                        'text-background-opacity': 0.85,
                        'text-background-shape': 'roundrectangle',
                    })
                .selector("node[type='chemical'][target_chemical=1]")
                    .css({
                        'background-color': '#C60800',
                        'border-color': '#C60800',
                    })
                .selector("node[type='chemical'][target_chemical=0]")
                    .css({
                        'background-color': '#52be80',
                        'border-color': '#52be80',
                    })
                .selector("node[type='chemical'][?svg]")  // The beauty of it: "?" will match only non null values
                    .css({
                        'background-image': 'data(svg)',
                        'background-fit': 'contain',
                        'border-width': 5,
                    })
                .selector('edge')
                    .css({
                        'curve-style': 'bezier',
                        'line-color': 'darkgray',
                        'width': '5px',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': 'darkgray',
                        'arrow-scale' : 2
                    })                    
                .selector('.faded')
                    .css({
                        'opacity': 0.15,
                        'text-opacity': 0.25
                    })
                .selector('.highlighted')
                    .css({
                        'width': '9px'
                    })
                .selector('node:selected')
                    .css({
                        'border-width': 5,
                        'border-color': 'black'
                    })
        );
        
        cy.on('tap', 'node', function(evt){
            let node = evt.target;
            // Dump into console
            console.log(node.data());
            // Print info
            if (node.is('[type = "chemical"]')){
                panel_startup_info(false);
                panel_reaction_info(null, false);
                panel_pathway_info(null, false);
                panel_chemical_info(node, true);
            } else if (node.is('[type = "reaction"]')){
                panel_startup_info(false);
                panel_chemical_info(null, false);
                panel_pathway_info(null, false);
                panel_reaction_info(node, true);
            }
        });

        cy.on('tap', 'edge', function(evt){
            let edge = evt.target;
            console.log(edge.data());
        });
        
    }
    
    /** Trigger a layout rendering
     */
    function render_layout(){
        cy.minZoom(1e-50);
        cy.on('layoutstop', function(e){
            cy.minZoom(cy.zoom());
        });
        let lay = cy.layout({
            name: 'breadthfirst',
            roots: cy.elements("node[target_chemical = 1]")
        });
        lay.run();
    }
        
    /** Load a metabolic network
     *
     * Only nodes and edges involved in 'selected_paths' will be displayed.
     *
     * @param selected_paths (array or str): path IDs or special flags
     */
    function show_pathways(selected_paths='__ALL__'){
      
        if (selected_paths == '__ALL__'){
            cy.nodes().css({visibility: 'visible'});
            cy.edges().css({visibility: 'visible'});
        } else if (selected_paths == '__NONE__'){
            cy.nodes().css({visibility: 'hidden'});
            cy.edges().css({visibility: 'hidden'});
        } else {
            // Nodes
            cy.nodes().forEach(function(node, index){
                let node_paths = node.data('path_ids');
                if (share_at_least_one(node_paths, selected_paths)){
                    node.css({visibility:'visible'});
                } else {
                    node.css({visibility:'hidden'});
                }
            });
            // Edges
            cy.edges().forEach(function(edge, index){
                let edge_paths = edge.data('path_ids');
                if (share_at_least_one(edge_paths, selected_paths)){
                    edge.css({visibility:'visible'});
                } else {
                    edge.css({visibility:'hidden'});
                }
            });
        }
    }

    /** Handle cofactor display
     *
     * Hide of show all nodes annotated as cofactor
     *
     * @param show (bool): will show cofactors if true
     */
    function show_cofactors(show=true){
        if (show){
            cy.add(cofactor_collection);
            render_layout();
        } else {
            cy.remove(cofactor_collection);
            render_layout();
        }
    }

    /**
     * Make the pathway table sortable
     */
    function make_pathway_table_sortable(){
        $("#table_choice > table").tablesorter({
            theme : 'default',
            sortList: [[4,1],[0,0]],  // Sort on the fourth column (descending) and then on the first column (ascending order)
            headers : {  // Disable sorting for these columns
                '.path_checkbox_head, .path_info_head, .path_colour_head': {
                    sorter: false
                }
            }
        });
    }
    
    // When a pathway is checked
    $("input[name=path_checkbox]").change(function(){
        selected_paths = get_checked_pathways();
        show_pathways(selected_paths);
    });
    
    /** 
     * Pathway visibility is updated when a pathway label is hovered
     * 
     * Note: the hover CSS is handled in the CSS file.
     * Node: some vocabulary precisions, pinned stands for path ID locked "on",
     *      while highlighted stands for the path ID currently hovered
     */
    $("td.path_id").hover(function(){
        let path_id = $(this).data('path_id');
        path_handler.highlight_pathways([path_id]);
    }, function(){
        path_handler.highlight_pathways([]);
        path_handler.update_pinned_paths_visibility();
    });
    
    /**
     * Pathway are pinned on click
     */
    $("td.path_id").click(function(){
        let path_id = $(this).data('path_id');
        if ($(this).hasClass('pinned')){
            path_handler.remove_pinned_paths([path_id]);
            path_handler.update_pinned_paths_visibility();
            $(this).removeClass('pinned');
        } else {
            path_handler.add_pinned_paths([path_id]);
            path_handler.update_pinned_paths_visibility();
            $(this).addClass('pinned');
        }
    });
    
    // When a pathway "info" is clicked
    $("td.path_info").click(function(){
        path_id = $(this).data('path_id');
        panel_startup_info(false);
        panel_chemical_info(null, false);
        panel_reaction_info(null, false);
        panel_pathway_info(path_id, true);
    });
        
    // Pathways selection
    $('#hide_all_pathways_button').on('click', function(event){
        show_pathways(selected_paths='__NONE__');  // Hide all
        $('input[name=path_checkbox]').prop('checked', false);  // Uncheck all
    });
    $('#view_all_pathways_button').on('click', function(event){
        show_pathways(selected_paths='__ALL__');  // Show all
        $('input[name=path_checkbox]').prop('checked', true);  // Check all
    });
    
    // Cofactors handling
    $('#show_cofactors_button').on('click', function(event){
        show_cofactors(true);
        // Update visible pathways to update their cofactor nodes visibility
        selected_paths = get_checked_pathways();
        show_pathways(selected_paths);
        // Update hilighted pathways to update their cofactor nodes status
        path_handler.update_pinned_paths_visibility();
    });
    $('#remove_cofactors_button').on('click', function(event){
        show_cofactors(false);
    });
    
    // Manual colour handling
    colour_pickers = document.querySelectorAll(".path_colour");
    for (let i = 0; i < colour_pickers.length; i++){
        colour_pickers[i].addEventListener("input", live_update_colour, false);
    }
    
    /**
     * Set the colour of all edges involved in a pathway
     *
     * @param event: event related to a pathway
     */
    function live_update_colour(event) {
        let path_id = $(this).data('path_id');
        edges = get_edges_from_path_id(path_id, cy);
        edges.style({
            'line-color': event.target.value,
            'target-arrow-color': event.target.value
        });
    }

    /**
     * 
     * Fill table values
     * 
     * @param score_label (str): the score label to use within the path info
     */
    function put_pathway_values(score_label='global_score'){
        for (let path_id in pathways_info){
            // Collect the value
            let score = pathways_info[path_id]['scores'][score_label];
            if (! isNaN(score)){
                score = parseFloat(score).toFixed(3);
            } else {
                score = 'NaN';
            }
            // Push it into the pathway table
            let path_td = $('td.path_value[data-path_id=' + path_id + ']');
            path_td.html(score);
            
        }
    }

});
