import pandas as pd
import os
import plotly.io as pio
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output
import base64

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

# Load image safely with fallback
image_path = os.path.join("data", "aei_logo.png")
encoded_image = None
if os.path.exists(image_path):
    with open(image_path, 'rb') as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()

pio.templates.default = "plotly_white"

CURR_PATH = os.path.abspath(os.path.dirname(__file__))

def load_data(filename):
    path = os.path.join(CURR_PATH, "data", filename)
    return pd.read_csv(path)

budget_df = load_data("budget_estimates.csv")
poverty_df = load_data("poverty_estimates.csv")
dists_df = load_data("dist_estimates.csv")
params_df = load_data("params_data.csv")

def filter_data(df, policy, refund, ctc_c, u6_bonus, ps):
    if policy in ["cl", "tcja", "house25", "senate25"]:
        lookup = {
            "cl": "CL",           # Current Law (TCJA expires)
            "tcja": "TCJA",       # TCJA Extension
            "house25": "House25", # House OBBB
            "senate25": "Senate25" # Senate OBBB
        }
        return df[df["type"] == lookup[policy]]
    elif policy == "custom":
        return df[
            (df["type"] == refund)
            & (df["ctc_c"] == ctc_c)
            & (df["u6_bonus"] == u6_bonus)
            & (df["ps"] == ps)
        ]
    return pd.DataFrame()

def build_summary_table(base_vals, reform_vals):
    headers = ['', 'Baseline Policy', 'Reform Policy', 'Difference']
    rows = [
        ('Annual Value of All Child Tax Benefits (2025 $)', base_vals['value_all'], reform_vals['value_all']),
        ('Annual Value of Child Tax Credit (2025 $)', base_vals['value_ctc'], reform_vals['value_ctc']),
        ('Average Total Benefit ($)', base_vals['mean'], reform_vals['mean']),
        ('Percent Change in After-Tax Income (%)', base_vals['pc_aftertaxinc'], reform_vals['pc_aftertaxinc']),
        ('EMTR on Labor (%)', base_vals['metr_reform'], reform_vals['metr_reform']),
        ('SPM Poverty Rate - Total U.S. (%)', base_vals['spm_all'], reform_vals['spm_all']),
        ('SPM Poverty Rate - Under 18 (%)', base_vals['spm_u18'], reform_vals['spm_u18'])
    ]
    cells = [list(zip(*rows))[0],
             [v for v in list(zip(*rows))[1]],
             [v for v in list(zip(*rows))[2]],
             [round(r - b, 1) for b, r in zip(list(zip(*rows))[1], list(zip(*rows))[2])]]

    fig = go.Figure(data=[go.Table(
        columnorder=[1, 2, 3, 4], columnwidth=[60, 14, 14, 12],
        header=dict(values=headers, fill_color='#008CCC', font=dict(color='white', size=14), height=30),
        cells=dict(values=cells, fill_color='#F9F9F9', font=dict(color='#414141', size=14), height=30, align=['left', 'center'])
    )])
    fig.update_layout(title={"text": 'Comparing Baseline and Reform', 'y': 0.9, 'x': 0.5, 'xanchor': 'center'})
    return fig

def build_param_table(base_vals, reform_vals):
    headers = ['', 'Baseline Policy', 'Reform Policy']
    rows = [
        ('Maximum Credit Amount', base_vals['max_c'], reform_vals['max_c']),
        ('Bonus Under 6', base_vals['bon6'], reform_vals['bon6']),
        ('Max Refundable Amount', base_vals['max_r'], reform_vals['max_r']),
        ('Qualifying Ages', base_vals['q_age'], reform_vals['q_age']),
        ('Refund Threshold', base_vals['thresh'], reform_vals['thresh']),
        ('Phase-In Rate', base_vals['pir'], reform_vals['pir']),
        ('Phaseout Start', base_vals['pos'], reform_vals['pos']),
        ('Phaseout Rate', base_vals['por'], reform_vals['por'])
    ]
    cells = [list(zip(*rows))[0], [v for v in list(zip(*rows))[1]], [v for v in list(zip(*rows))[2]]]

    fig = go.Figure(data=[go.Table(
        columnorder=[1, 2, 3], columnwidth=[40, 30, 30],
        header=dict(values=headers, fill_color='#008CCC', font=dict(color='white', size=14), height=30),
        cells=dict(values=cells, fill_color='#F9F9F9', font=dict(color='#414141', size=13), height=26, align=['left', 'center'])
    )])
    fig.update_layout(title={"text": 'Policy Parameters', 'y': 0.9, 'x': 0.5, 'xanchor': 'center'})
    return fig

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    html.Div([html.Img(src=f"data:image/png;base64,{encoded_image}" if encoded_image else "", height=80)]),
    html.H3("Child Tax Credit Reform Dashboard"),

    html.Label("Baseline Policy"),
    dcc.Dropdown(id="base", options=[
        {"label": "Current Policy", "value": "cl"},
        {"label": "TCJA Extension", "value": "tcja"},
        {"label": "House OBBB 2025", "value": "house25"},
        {"label": "Senate OBBB 2025", "value": "senate25"}
    ], value="cl", clearable=False),

    html.Label("Reform Policy"),
    dcc.Dropdown(id="reform", options=[
        {"label": "TCJA Extension", "value": "tcja"},
        {"label": "House OBBB 2025", "value": "house25"},
        {"label": "Senate OBBB 2025", "value": "senate25"},
        {"label": "Custom CTC Reform", "value": "custom"}
    ], value="tcja", clearable=False),

    html.Div(id='custom-container', children=[
        html.Label("Max Credit Value"),
        dcc.Dropdown(id="ctc_c", options=[
            {"label": "$2000", "value": 2000},
            {"label": "$2200", "value": 2200},
            {"label": "$2500", "value": 2500},
            {"label": "$3000", "value": 3000},
            {"label": "$3500", "value": 3500},
        ], value=2000, clearable=False),

        html.Label("Bonus Under 6"),
        dcc.Dropdown(id="u6_bonus", options=[
            {"label": "$0", "value": 0},
            {"label": "$500", "value": 500},
            {"label": "$1000", "value": 1000},
        ], value=0, clearable=False),

        html.Label("Refundability"),
        dcc.Dropdown(id="refund", options=[
            {"label": "Non-Refundable", "value": "Nonref"},
            {"label": "Fully Refundable", "value": "Refund"},
        ], value="Nonref", clearable=False),

        html.Label("Phaseout Start"),
        dcc.Dropdown(id="ps", options=[
            {"label": "Pre-TCJA", "value": "PT"},
            {"label": "Current Policy", "value": "CL"},
            {"label": "Eliminate Phaseout", "value": "NO"},
        ], value="CL", clearable=False),
    ], style={"display": "none"}),

    dcc.Tabs(id="tabs", value="summary_tab", children=[
        dcc.Tab(label="Summary", value="summary_tab"),
        dcc.Tab(label="Parameters", value="params_tab"),
    ]),

    dcc.Graph(id="main-graph"),
])

@app.callback(Output('custom-container', 'style'), Input('reform', 'value'))
def toggle_custom(reform):
    return {'display': 'block'} if reform == 'custom' else {'display': 'none'}

@app.callback(
    Output("main-graph", "figure"),
    Input("base", "value"), Input("reform", "value"), Input("refund", "value"),
    Input("ctc_c", "value"), Input("u6_bonus", "value"), Input("ps", "value"),
    Input("tabs", "value")
)
def update_graph(base, reform, refund, ctc_c, u6_bonus, ps, tabs):
    base_bud = filter_data(budget_df, base, refund, ctc_c, u6_bonus, ps)
    reform_bud = filter_data(budget_df, reform, refund, ctc_c, u6_bonus, ps)
    base_pov = filter_data(poverty_df, base, refund, ctc_c, u6_bonus, ps)
    reform_pov = filter_data(poverty_df, reform, refund, ctc_c, u6_bonus, ps)
    base_fig = filter_data(dists_df, base, refund, ctc_c, u6_bonus, ps)
    reform_fig = filter_data(dists_df, reform, refund, ctc_c, u6_bonus, ps)
    base_param = filter_data(params_df, base, refund, ctc_c, u6_bonus, ps)
    reform_param = filter_data(params_df, reform, refund, ctc_c, u6_bonus, ps)

    base_vals = {
        'value_all': base_bud['value_all'].values[0],
        'value_ctc': base_bud['value_ctc'].values[0],
        'mean': base_fig[base_fig['decile']=="ALL"]['mean'].values[0],
        'pc_aftertaxinc': base_fig[base_fig['decile']=="ALL"]['pc_aftertaxinc'].values[0],
        'metr_reform': base_fig[base_fig['decile']=="ALL"]['metr_reform'].values[0],
        'spm_all': base_pov['spm_all'].values[0],
        'spm_u18': base_pov['spm_u18'].values[0],
        'max_c': base_param['max_c'].values[0],
        'bon6': base_param['bon6'].values[0],
        'max_r': base_param['max_r'].values[0],
        'q_age': base_param['q_age'].values[0],
        'thresh': base_param['thresh'].values[0],
        'pir': base_param['pir'].values[0],
        'pos': base_param['pos'].values[0],
        'por': base_param['por'].values[0],
    }

    reform_vals = {
        'value_all': reform_bud['value_all'].values[0],
        'value_ctc': reform_bud['value_ctc'].values[0],
        'mean': reform_fig[reform_fig['decile']=="ALL"]['mean'].values[0],
        'pc_aftertaxinc': reform_fig[reform_fig['decile']=="ALL"]['pc_aftertaxinc'].values[0],
        'metr_reform': reform_fig[reform_fig['decile']=="ALL"]['metr_reform'].values[0],
        'spm_all': reform_pov['spm_all'].values[0],
        'spm_u18': reform_pov['spm_u18'].values[0],
        'max_c': reform_param['max_c'].values[0],
        'bon6': reform_param['bon6'].values[0],
        'max_r': reform_param['max_r'].values[0],
        'q_age': reform_param['q_age'].values[0],
        'thresh': reform_param['thresh'].values[0],
        'pir': reform_param['pir'].values[0],
        'pos': reform_param['pos'].values[0],
        'por': reform_param['por'].values[0],
    }

    if tabs == "summary_tab":
        return build_summary_table(base_vals, reform_vals)
    else:
        return build_param_table(base_vals, reform_vals)

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8050)))
