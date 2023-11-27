import sqlite3
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from collections import Counter, defaultdict
import plotly.express as px
from wordcloud import WordCloud
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import plotly.graph_objects as go

# Constants
DB_FILE_PATH = "database/harmony.db"
FACE_IMG_PATH = "media/face.png"
MUSIC_IMG_PATH = "media/music.png"

def fetch_data():
    # Connect to the SQLite database and fetch data
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT full_name FROM composers")
    composers_data = cursor.fetchall()

    cursor.execute('''SELECT 
                    compositions.full_name,
                    compositions.work_title,
                    composers.full_name AS composer_name, 
                    keys.name AS key, 
                    instrumentations.name AS instrumentation, 
                    styles.name AS piece_style, 
                    languages.name AS language
                  FROM compositions
                    LEFT JOIN composers ON compositions.composer_id = composers.id
                    LEFT JOIN keys ON compositions.key_id = keys.id
                    LEFT JOIN instrumentations ON compositions.instrumentation_id = instrumentations.id
                    LEFT JOIN styles ON compositions.piece_style_id = styles.id
                    LEFT JOIN languages ON compositions.language_id = languages.id''')

    compositions_data = cursor.fetchall()

    conn.close()

    return composers_data, compositions_data

def extract_data(composers_data, compositions_data):
    # Extract nested information with error handling
    composers = [{"full_name": entry[0]} for entry in composers_data]
    compositions = [{key: value if value is not None else "" for key, value in zip(["full_name", "Work Title", "composer", "Key", "Instrumentation", "Piece Style", "Language"], entry)} for entry in compositions_data]
    composer_names = [entry["full_name"] for entry in composers]
    composition_names = [entry["Work Title"] for entry in compositions]

    return composers, compositions, composer_names, composition_names

def create_dash_app():
    # Create Dash App
    app = Dash(__name__)

    app.layout = html.Div([
        dcc.Loading(
            id="loading-container",
            type="dot",
            fullscreen=True,
            color="lightsteelblue",
            children=[
                html.Div([
                    dcc.Dropdown(
                        id='visualization-dropdown',
                        options=[
                            {'label': 'Composer Names Word Cloud', 'value': 'composer_names_wordcloud'},
                            {'label': 'Composition Names Word Cloud', 'value': 'composition_names_wordcloud'},
                            {'label': 'Top 10 Categories', 'value': 'top_10'},
                            {'label': 'Instrumentations In Styles', 'value': 'frequency_Piece Style_Instrumentation'},
                            {'label': 'Authors In Styles', 'value': 'frequency_Piece Style_composer'},
                            {'label': 'Keys In Styles', 'value': 'frequency_Piece Style_Key'}
                        ],
                        value='composer_names_wordcloud',
                        clearable=False
                    ), 
                    html.Div(id="visualization-container"),
                ], style={'width': '50%', 'margin': '10px auto', 'color': '#333', 'font-family': '"Open Sans", verdana, arial, sans-serif', 'font-size': '12px'}),
                
                html.Div([
                    dcc.Dropdown(
                        id='sub-dropdown',
                        options=[
                            {'label': 'Most Productive Composers', 'value': 'composer'},
                            {'label': 'Most Popular Keys', 'value': 'Key'},
                            {'label': 'Most Popular Instrumentation', 'value': 'Instrumentation'},
                            {'label': 'Most Popular Styles', 'value': 'Piece Style'},
                        ],
                        multi=False,
                        value='composer',
                        style={'display' : 'none'},
                        clearable=False
                    ), 
                    html.Div(id="sub-dropdown-container"),
                ], style={'width': '50%', 'margin': '10px auto', 'color': '#333', 'font-family': '"Open Sans", verdana, arial, sans-serif', 'font-size': '12px'}),

                html.Div(id='visualization-output', style={'text-align': 'center'}),
            ],
        ),
    ])

    return app

# Create the Dash App
app = create_dash_app()

# Fetch and extract data
composers_data, compositions_data = fetch_data()
composers, compositions, composer_names, composition_names = extract_data(composers_data, compositions_data)

# Wordcloud face mask
face_mask = np.array(Image.open(FACE_IMG_PATH))
# Wordcloud music mask
music_mask = np.array(Image.open(MUSIC_IMG_PATH))

def generate_wordcloud(title, category):
    data = composer_names if category == "composer" else composition_names
    mask = face_mask if category == 'composer' else music_mask
    wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='twilight', mask=mask, collocations=False).generate(' '.join(data))
    image_stream = BytesIO()
    wordcloud.to_image().save(image_stream, format='PNG')
    encoded_image = base64.b64encode(image_stream.getvalue()).decode('utf-8')
    return html.Img(src=f'data:image/png;base64,{encoded_image}', alt=title, style={'max-width': '100%', 'margin': '20px auto', 'border-radius': '10px'})

def generate_top_10(category):
    category_data = [entry[category] for entry in compositions]
    top_data = Counter(category_data).most_common(10)
    category_string = category.capitalize()

    fig = px.scatter(x=[item[0] for item in top_data], y=[item[1] for item in top_data],
                     labels={'x': f'<b>{category_string}</b>', 'y': '<b>Number of Compositions</b>'},
                     template="seaborn",
                     text=[f"{item[0]}: {item[1]}" for item in top_data],
                     hover_name=[f"{item[0]}: {item[1]}" for item in top_data],
                     )
    
    fig.update_traces(mode='markers', marker=dict(symbol='circle', size=14, color='lightsteelblue'))
    
    fig.update_layout(
        xaxis=dict(
            title=dict(text=f'<b>{category_string}s</b>', font=dict(size=12, color='darkgray', family='"Open Sans", verdana, arial, sans-serif')),
            tickfont=dict(size=10, color='gray', family='"Open Sans", verdana, arial, sans-serif'),
        ),
        yaxis=dict(
            title=dict(text=f'<b>Number of Compositions</b>', font=dict(size=12, color='darkgray', family='"Open Sans", verdana, arial, sans-serif')),
            tickfont=dict(size=10, color='gray', family='"Open Sans", verdana, arial, sans-serif'),
        )
    )

    return dcc.Graph(figure=fig, style={'width': '80%', 'margin': '20px auto', 'border-radius': '10px', 'color': '#333'})

def generate_frequency(x_key, y_key):
    counts_per_x = defaultdict(Counter)

    for entry in compositions:
        x_val = entry[x_key]
        y_val = entry[y_key]

        if x_val and y_val:
            counts_per_x[x_val][y_val] += 1

    non_empty_x_values = [x_val for x_val, counts in counts_per_x.items() if any(counts.values())]
    non_empty_y_values = set(y_val for counts in counts_per_x.values() for y_val, count in counts.items() if count > 0)

    fig = go.Figure()

    for i, y_val in enumerate(non_empty_y_values):
        y_counts = [counts[y_val] for x_val, counts in counts_per_x.items() if x_val in non_empty_x_values]

        if any(y_counts):
            gradient_color = f'hsl({i * (360 / len(non_empty_y_values))}, 50%, 50%)'
            fig.add_trace(go.Bar(x=non_empty_x_values, y=y_counts, name=str(y_val), marker_color=gradient_color))

    fig.update_layout(
        barmode="stack",
        xaxis=dict(
            title=dict(text=f'<b>{x_key.capitalize()}s</b>', font=dict(size=12, color='darkgray', family='"Open Sans", verdana, arial, sans-serif')),
            tickfont=dict(size=10, color='gray', family='"Open Sans", verdana, arial, sans-serif')
        ),
        yaxis=dict(
            title=dict(text=f'<b>{y_key.capitalize()}s</b>', font=dict(size=12, color='darkgray', family='"Open Sans", verdana, arial, sans-serif')),
            tickfont=dict(size=10, color='gray', family='"Open Sans", verdana, arial, sans-serif'),
        ),
        height=900,
        showlegend=False,
        bargap=0.1,
        bargroupgap=0.0,
        template="seaborn"
    )

    return dcc.Graph(figure=fig, style={'width': '90%', 'margin': '10px auto', 'border-radius': '10px', 'color': '#333'})

# Callback to update the visualization based on dropdown selection
@app.callback(
    [Output('visualization-output', 'children'),
     Output('sub-dropdown', 'style')],
    [Input('visualization-dropdown', 'value'),
     Input('sub-dropdown', 'value')]
)
def update_visualization(selected_option, selected_sub_option):
    if selected_option == 'composer_names_wordcloud':
        return generate_wordcloud('Composer Names Word Cloud', 'composer'), {'display': 'none'}
    elif selected_option == 'composition_names_wordcloud':
        return generate_wordcloud('Piece Titles Word Cloud', 'composition'), {'display': 'none'}
    elif selected_option == 'top_10':
        return generate_top_10(selected_sub_option), {'display': ''}
    elif selected_option.startswith('frequency'):
        option_parts = selected_option.split('_')
        type_value, x_key, y_key = option_parts
        return generate_frequency(x_key, y_key), {'display': 'none'}
    else:
        return None, {'display': 'none'}

# Run the app
if __name__ == "__main__":
    app.run_server(debug=False)