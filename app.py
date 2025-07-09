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

def filter_data(df, policy, refund, ctc_c, ps):
    lookup = {
        "cl": "CL",           # Current Law (TCJA expires)
        "tcja": "TCJA",       # TCJA Extension
        "house25": "House25", # House OBBB
        "senate25": "Senate25" # Senate OBBB
    }
    if policy in lookup:
        filtered_df = df[df["type"] == lookup[policy]]
        if filtered_df.empty:
            print(f"⚠️ Warning: No data found for policy '{lookup[policy]}'")
        return filtered_df
    elif policy == "custom":
        filtered_df = df[(df["type"] == refund) & (df["ctc_c"] == ctc_c) & (df["ps"] == ps)]
        if filtered_df.empty:
            print("⚠️ Warning: No data found for custom reform with given parameters")
        return filtered_df
    else:
        print("⚠️ Warning: Unknown policy selected")
        return pd.DataFrame()

def build_summary_table(base_vals, reform_vals):
    headers = ['', 'Baseline Policy', 'Reform Policy', 'Difference']
    rows = [
        ('Annual Value of Child Tax Credit (2025 $Billions)', base_vals['value_ctc'], reform_vals['value_ctc']),
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
        cells=dict(values=cells, fill_color='#F9F9F9', font=dict(color='#414141', size=14),
                   height=30, align=['left', 'center'])
    )])

    # Add a note below the table
    fig.add_annotation(
        text="*For this version of the calculator, it assumes that the TCJA expired and was never extended as the current law.*",
        showarrow=False,
        xref="paper", yref="paper",
        x=0, y=-0.2,
        xanchor="left", yanchor="top",
        font=dict(size=12, color='gray')
    )

    return fig

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# App layout
app.layout = html.Div([
    html.Div([
        html.Img(src="data:image/png;base64,{}".format(encoded_image), style={'width': '200px'}),
        html.H1("Child Tax Credit Reform Dashboard", style={'textAlign': 'center'})
    ]),
    html.Div([
        html.Label("Select Baseline Policy:"),
        dcc.Dropdown(
            id='baseline-policy',
            options=[
                {"label": "Current Policy (TCJA Expires)", "value": "cl"},
                {"label": "TCJA Extension", "value": "tcja"}
            ],
            value="cl"
        ),
        html.Label("Select Reform Policy:"),
        dcc.Dropdown(
            id='reform-policy',
            options=[
                {"label": "TCJA Extension", "value": "tcja"},
                {"label": "House Reform", "value": "house25"},
                {"label": "Senate Reform", "value": "senate25"},
                {"label": "Custom Reform", "value": "custom"}
            ],
            value="tcja"
        ),
        html.Br(),
        html.Div(id="summary-table"),
    ])
])

@app.callback(
    Output('summary-table', 'children'),
    Input('baseline-policy', 'value'),
    Input('reform-policy', 'value')
)
def update_dashboard(baseline_policy, reform_policy):
    base_df = filter_data(budget_df, baseline_policy, None, None, None)
    reform_df = filter_data(budget_df, reform_policy, None, None, None)

    if base_df.empty or reform_df.empty:
        return html.P("⚠️ No data available for selected policies.")

    base_vals = base_df.iloc[0].to_dict()
    reform_vals = reform_df.iloc[0].to_dict()
    table_fig = build_summary_table(base_vals, reform_vals)
    return dcc.Graph(figure=table_fig)

if __name__ == '__main__':
    app.run_server(debug=True)
