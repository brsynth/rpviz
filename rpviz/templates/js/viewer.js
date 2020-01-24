/*jshint esversion: 6 */

//__author__: Thomas Duigou (thomas.duigou@inra.fr)
//__date__: 2019.12.09
//__license : MIT
//__note__ : based on Scope Viewer and Annaelle Baudier's work


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
    init_network(true);
    render_layout();
    
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
                        'width': 90,
                        'background-color': 'white',
                        'border-width': 5,
                        'border-color': 'darkgray',
                        'border-style': 'solid',
                        'content': 'data(short_label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'text-opacity': 1,
                        'color': '#575757',
                        'font-size': '12px',
                    })
                .selector("node[type='chemical']")
                    .css({
                        'background-color': '#52be80',
                        'background-fit':'contain',
                        'shape': 'roundrectangle',
                        'width': 80,
                        'height': 80,
                        'label': 'data(short_label)',
                        'font-size': '22px',
                        'font-weight': 'bold',
                        'text-valign': 'bottom',
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
                .selector("node[type='chemical'][svg]")
                    .css({
                        'background-image': 'data(svg)',
                        'background-fit': 'contain',
                        'border-width': 5,
                    })
                .selector('edge')
                    .css({
                        'curve-style': 'bezier',
                        'line-color': 'darkgray',
                        'width': '4px',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': 'darkgray',
                        'arrow-scale' : 2
                    })                    
                .selector('.faded')
                    .css({
                        'opacity': 0.15,
                        'text-opacity': 0.25
                    })
                .selector('.highlighted_more')
                    .css({
                        'width': '7px',
                        'line-color': 'gray',
                        'target-arrow-color': 'gray',
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
                panel_chemical_info(node, true);
            } else if (node.is('[type = "reaction"]')){
                panel_startup_info(false);
                panel_chemical_info(null, false);
                panel_reaction_info(node, true);
            }
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
    
    /**
     * Make compound labels
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
     * Make reaction labels
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
     * Highlight a pathway
     *
     * @param path_ids (array): path IDs
     */
    function highlight_pathways(path_ids){
        if (path_ids == '__ALL__'){
            cy.nodes().removeClass('faded');
            cy.edges().removeClass('faded');
        } else {
            // Nodes
            cy.nodes().forEach(function(node, index){
                let node_paths = node.data('path_ids');
                if (share_at_least_one(node_paths, path_ids)){
                    node.removeClass('faded');
                } else {
                    node.addClass('faded');
                }
            });
            // Edges
            cy.edges().forEach(function(edge, index){
                let edge_paths = edge.data('path_ids');
                if (share_at_least_one(edge_paths, path_ids)){
                    edge.removeClass('faded');
                } else {
                    edge.addClass('faded');
                }
            });
        }
    }
    
    /**
     * Highlight a pathway even more by magnifying edges
     *
     * @param path_id (array): the unique path ID to highlight more
     */
    function highlight_pathway_more(path_id){
        if (path_id == '__NONE__'){
            cy.edges().removeClass('highlighted_more');
        } else {
            // Edges
            cy.edges().forEach(function(edge, index){
                let edge_paths = edge.data('path_ids');
                if (share_at_least_one(edge_paths, [path_id])){
                    edge.addClass('highlighted_more');
                } else {
                    edge.removeClass('highlighted_more');
                }
            });
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
            $("span.chem_info_inchikey").html(inchikey);
            $("span.chem_info_inchi").html(inchi);
            $("span.chem_info_smiles").html(smiles);
            $("span.chem_info_iscofactor").html(cofactor);
            // Inject SVG depiction as a background image
            $('div.chem_info_svg').css('background-image', "url('" + svg + "')");
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
            // Show
            $("#panel_reaction_info").show();
        } else {
            $("#panel_reaction_info").hide();
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
     * Build the pathway table
     *
     * Derived from: http://jsfiddle.net/manishmmulani/7MRx6
     */
    function build_pathway_table(){
        console.assert(pathways_info);
        
        // Table skeleton
        let table_base = $('<table></table>');
        
        // Build the header
        let field_names = ['Show', 'Pathway', 'Colour'];
        let table_row = $('<tr></tr>');
        for (let i = 0; i < field_names.length; i++){
            let value = field_names[i];
            table_row.append($('<th></th>').html(value));
        }
        table_base.append($('<thead></thead>').append(table_row));
        
        // Build the body
        let table_body = $('<tbody></tbody>');
        for (let path_id in pathways_info){
            let info = pathways_info[path_id];
            let table_row = $('<tr></tr>');
            table_row.append($('<td class="checkbox"></td>').append($('<input type="checkbox" name="path_checkbox" value=' + path_id + '>')));
            table_row.append($('<td class="path_id" data-path_id="' + path_id + '"></td>').html(path_id));
            table_row.append($('<td class="path_colour" data-path_id="' + path_id + '"><input type="color" name="head" value="#A9A9A9"></td>'));
            table_body.append(table_row);
        }
        table_base.append(table_body);

        //Finally
        $("#table_choice").append(table_base);
    }
    
    /**
     * Collect pinned pathways IDs
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
    
    // When a pathway is checked
    $("input[name=path_checkbox]").change(function(){
        selected_paths = get_checked_pathways();
        show_pathways(selected_paths);
    });
    
    /** Pathway visibility is updated when a pathway label is hovered
     *
     * Note: the hover CSS is handled in the CSS file.
     * Node: some vocabulary precisions, pinned stands for path ID locked "on",
     *      while highlighted stands for the path ID currently hovered
     */
    $("td.path_id").hover(function(){
        // Nodes and edges covering to oinned + highlighted paths
        let pinned_paths = get_pinned_pathway_IDs();
        let current_path = $(this).data('path_id');
        let path_ids = pinned_paths.concat([current_path]);  // Add the hovered one
        highlight_pathways(path_ids);
        // Edges corresponding to the highlithted path
        highlight_pathway_more(current_path);
    }, function(){
        let current_path = $(this).data('path_id');
        highlight_pathway_more('__NONE__');
        let pinned_paths = get_pinned_pathway_IDs();
        if (pinned_paths.length > 0){
            highlight_pathways(pinned_paths);
        } else {
            highlight_pathways('__ALL__');
        }
    });
    
    // When a pathway label is clicked
    $("td.path_id").click(function(){
        if ($(this).hasClass('pinned')){
            $(this).removeClass('pinned');
        } else {
            $(this).addClass('pinned');
        }
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
        pinned_paths = get_pinned_pathway_IDs();
        if (pinned_paths.length > 0){
            highlight_pathways(path_ids=pinned_paths);
        } else {
            highlight_pathways(path_ids='__ALL__');
        }
    });
    $('#remove_cofactors_button').on('click', function(event){
        show_cofactors(false);
    });
    
    // Manal colour handling
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
        edges = get_edges_from_path_id(path_id);
        edges_col.style({
            'line-color': event.target.value,
            'target-arrow-color': event.target.value
        });
    }


    /**
     * Get the collection of edges involved in a given path_id
     *
     * @param path_id (str): pathway ID
     */
    function get_edges_from_path_id(path_id){
        edges_col = cy.collection();
        cy.edges().forEach(function(edge, index){
            let edge_path_ids = edge.data('path_ids');
            if (share_at_least_one(edge_path_ids, [path_id])){
                edges_col = edges_col.union(edge);
            }
        });
        return edges_col;
    }

});
