import dash
import dash_cytoscape as cyto
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import pandas as pd

cyto.load_extra_layouts()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

nodes_df = pd.read_csv('./data/nodes.csv')
edges_df = pd.read_csv('./data/edges.csv')

nodes = [
    {
        'data': {'id':n.id, 'topic':n.topic, 'text':n.text, 'link':n.link},
        'position': {'x':n.x, 'y':n.y},
        'locked': n.locked,
        'grabbable': n.grabbable
    } for n in nodes_df.itertuples()
]

edges = [
    {
        'data': {'source':e.source, 'target':e.target}
        
    } for e in edges_df.itertuples()
]


default_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'background-color': 'grey', 'shape': 'circle',
            # 'label': 'data(label)' # add field "label" in dataframe
        }
    },
    {
        'selector': '[topic = "Immigration"]',
        'style': {'background-color': 'pink'}
    },
    {
        'selector': '[topic = "Environment"]',
        'style': {'background-color': 'green'}
    },
    {
        'selector': '[topic = "Local politics"]',
        'style': {'background-color': 'red'}
    },
    {
        'selector': '[topic = "Death penalty"]',
        'style': {'background-color': 'black'}
    },
    {
        'selector': '[topic = "Education"]',
        'style': {'background-color': 'blue'}
    },
    {
        'selector': 'edge',
        'style': {'line-color': 'grey'}
    }   
]

topics_list = ["Local politics", "Death penalty", "Environment", "Education", "Immigration"]
topic_dropdown = dbc.Row(
    [
        dbc.Label("Topic", width=2),
        dcc.Dropdown(
            id='dropdown-select-topic',
            value=topics_list[0],
            clearable=False,
            options=[
                {'label': name.capitalize(), 'value': name}
                for name in topics_list
            ],
            style={"width": "100%"}
        ),
    ],
    className="mb-3",
)

text_input = dbc.Row(
    [
        dbc.Label("Text", width=2),
        dbc.Textarea(id='input-node-content', style={"width": "100%", "height": "50px"}),
    ],
    className="mb-3",
)

link_input = dbc.Row(
    [
        dbc.Label("Link", width=2),
        dcc.Textarea(id='input-node-url', style={"width": "100%", "height": "50px"}),
    ],
    className="mb-3",
)

add_btn = dbc.Row(
    [
        dbc.Button("Add Node", id='btn-add-node', color="primary", n_clicks_timestamp=0),
    ],
    className="mb-3",
)

form = dbc.Col([topic_dropdown, text_input, link_input, add_btn], width=2)
intro = dbc.Row(
    [
        dbc.Col([
            dcc.Markdown(
                """
            #####  \n\n
            ##### Explore / Add node data  
            Node color indicates its main topic.
            
            

            ##### \n\n
            """,
            style={"white-space": "pre"}
        )], width=10)
    ], justify="center"
)

graph = dbc.Col(
    [
        dbc.Row(
            [
                cyto.Cytoscape(
                    id="cytoscape-elements-callbacks",
                    layout={"name": "euler"},
                    style={"width": "100%", "height": "400px"},
                    elements=edges+nodes,
                    stylesheet=default_stylesheet,
                    minZoom=0.25,
                    maxZoom=1.5,
                )
            ]
        ),
        dbc.Row(
            [
                dbc.Alert(
                    id="node-data",
                    children="Click on a node to see its details here",
                    color="secondary",
                )
            ]
        ),
    ],
    width=8
)

navbar = dbc.NavbarSimple(
    [
        dbc.NavLink("About Project", id="info-toast-toggle", n_clicks=0, n_clicks_timestamp=0),
        dbc.Toast(
                "Each node on the graph is an idea/opinion, voice out your ideas/opinions by adding your own node! \
                    This graph was designed as a digital space for Singaporeans who  \
                    have diverse takes on issues pertaining to the nation.",
                id="info-toast",
                header="Project Info",
                is_open=False,
                dismissable=True,
                color="light",
                style={"position": "fixed", "top": 10, "left": 10, "width": 375, "font-size":16, "opacity":1},
            ),
        dbc.NavLink("Instructions", id="instruct-toast-toggle", n_clicks=0, n_clicks_timestamp=0),
        dbc.Toast(
                "Click on nodes to explore new ideas/opinions.\
                Follow the link in the node to see more details.\
                Add your own node using the form.",
                id="instruct-toast",
                header="Instructions",
                is_open=False,
                dismissable=True,
                color="light",
                style={"position": "fixed", "top": 10, "left": 10, "width": 375, "font-size":16, "opacity":1},
            )
    ],
    brand="Nation of Smarts",
    brand_href="#",
    color="primary",
    dark=True,
)

app.layout = html.Div([
        navbar,
        intro,
        dbc.Row([graph, form], justify="center"),
])


@app.callback(
    [Output("info-toast", "is_open"),Output("instruct-toast", "is_open")],
    Input("info-toast-toggle", "n_clicks_timestamp"),
    Input("instruct-toast-toggle", "n_clicks_timestamp")
)
def open_toast(info, instruct):
    if info>instruct:
        return [True, False]
    elif instruct>info:
        return [False, True]
    return [False, False]

@app.callback(Output('cytoscape-elements-callbacks', 'elements'),
              State('dropdown-select-topic', 'value'),
              State('input-node-content', 'value'),
              State('input-node-url', 'value'),
              Input('btn-add-node', 'n_clicks_timestamp'),
              State('cytoscape-elements-callbacks', 'elements'))
def update_elements(node_topic, node_content, node_url, btn_add, elements):
    current_nodes = get_current_nodes(elements)
    current_edges = get_valid_edges(current_nodes, elements)
    # If button was clicked and there is text input
    if int(btn_add) and node_topic and node_content and node_url:
        newId = int(get_highest_node_id(current_nodes))+1
        newNode = {
            'data': {'id':newId, 'topic':node_topic, 'text':node_content, 'link':node_url}, 
            'position': {'x':30,'y':-110}
        }
        source = find_topic_sources(newNode, current_nodes)[1]
        newEdge = {
            'data': {'source':int(source), 'target':int(newId)}
        }
        
        current_nodes.append(newNode)
        current_edges.append(newEdge)
        return current_edges + current_nodes

    # Default
    return elements

def get_highest_node_id(current_nodes):
    node_ids = [int(n['data']['id']) for n in current_nodes]
    return max(node_ids)

def find_topic_sources(new_node, all_nodes):
    node_topic = new_node['data']['topic']
    node_ids = []
    for n in all_nodes:
        if n['data']['topic'] == node_topic:
            node_ids.append(n['data']['id'])
    return node_ids
    

def get_valid_edges(current_nodes, elements):
    """Returns edges that are present in Cytoscape:
    its source and target nodes are still present in the graph.
    """
    valid_edges = []
    node_ids = {n['data']['id'] for n in current_nodes}

    for ele in elements:
        if 'source' in ele['data']:
            if ele['data']['source'] in node_ids and ele['data']['target'] in node_ids:
                valid_edges.append(ele)
    return valid_edges

def get_current_nodes(elements):
    """Returns nodes that are present in Cytoscape
    """
    current_nodes = []

    # get current graph nodes
    for ele in elements:
        # if the element is a node
        if 'source' not in ele['data']:
            current_nodes.append(ele)

    return current_nodes

@app.callback(
    Output("node-data", "children"), 
    [Input("cytoscape-elements-callbacks", "selectedNodeData")]
)
def display_nodedata(datalist):
    contents = "Click on a node to view new ideas/opinions"
    if datalist is not None:
        if len(datalist) > 0:
            data = datalist[-1]
            contents = []
            contents.append(html.H5("Topic: " + data["topic"].title()))
            if data["text"] != "This is a topic":
                contents.append(
                    html.P(
                        data["text"]
                    )
                )
                if data["link"] is not None:
                    contents.append(dcc.Link("See more details here", href=data["link"], target="_blank"))

    return contents

if __name__ == '__main__':
    app.run_server(debug=True)
