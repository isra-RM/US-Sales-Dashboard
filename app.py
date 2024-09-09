from pathlib import Path
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import altair as alt
import folium
import json
#from folium.plugins import HeatMap
from shiny import reactive
from shiny.express import render,input,ui
from shinywidgets import render_plotly,render_altair,render_widget
import calendar

#STYLING

ui.tags.style(
    """
    body {
        background-color: #5DADE2;
    }
    
    .modebar-container{
        display: none;
    }
    
    
    h2 {
        text-align : center;
        color: white;
        padding : 10px 20px;
        font-weight : bold;
        font-size : 50px ;
    }
    
    summary {
        display: none;
    }
    """
)


#FUNCTION TO APPLY STYLE TO PLOTLY GRAPHS

def style_plotly_chart(fig,yaxis_title):
    fig.update_layout(
        xaxis_title = '',
        yaxis_title = yaxis_title,
        plot_bgcolor = 'white',
        showlegend = False,
        coloraxis_showscale = False,
        font = {'family':'Arial','size':12}
    )
    fig.update_xaxes(
        showgrid = False
    )
    fig.update_yaxes(
        showgrid = False
    )
    return fig



ui.page_opts(title='Sales Dashboard for US Cities',fillable=False)

#READING DATA AND CALCULATING NEW USEFUL COLUMNS 

@reactive.calc
def dat():
    infile = Path(__file__).parent / "data/sales.csv"
    df = pd.read_csv(infile)
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['month'] = df['order_date'].dt.month_name()
    df['hour'] = df['order_date'].dt.hour
    df['day'] = df['order_date'].dt.day_name()
    df['value'] = df['quantity_ordered']*df['price_each']
    df['state'] = df['city'].apply(lambda x: re.findall(r'\((.*?)\)', x)[0])
    return df
   
#GENERAL LAYOUT OF THE DASHBOARD

with ui.card():
    ui.card_header("Sales by City in 2023")
    
    with ui.layout_sidebar(): 
        with ui.sidebar(bg="#f8f8f8",open='open'):  
            ui.input_selectize(
                "city",
                "Select a City:",
                [
                'Dallas (TX)',
                'Boston (MA)', 
                'Los Angeles (CA)',
                'San Francisco (CA)',
                'Seattle (WA)',
                'Atlanta (GA)',
                'New York City (NY)',
                'Portland (OR)',
                'Austin (TX)',
                'Portland (ME)'],
                multiple=False,
                selected = "Boston (MA)"
            )
        @render_altair
        def sales_over_time():
            df = dat()
            sales = df.groupby(['city','month'])['quantity_ordered'].sum().reset_index()
            sales_by_city = sales[sales['city'] == input.city()]
            month_order = calendar.month_name[1:]
            font_props = alt.Axis(labelFont="Arial",titleFont="Arial",labelFontSize=12,titleFontSize=15,tickSize=0,labelAngle=0)
            chart = alt.Chart(sales_by_city).mark_bar().encode(
              x = alt.X('month',sort=month_order,title='Month',axis=font_props),
              y = alt.Y('quantity_ordered',title='Quantity Ordered',axis=font_props),
              tooltip=['month','quantity_ordered']  
            ).properties(
                title = alt.Title(f"Sales over time -- {input.city()}")
            ).configure_axis(
                grid=False               
            ).configure_title(
                font = 'Arial',
                fontSize=18
            )
            
            return chart

with ui.layout_column_wrap(width=1/2):
    with ui.navset_card_underline( id='tab',footer=ui.input_numeric("n","Number of items",5,min=0,max=20)):
            with ui.nav_panel("Top Sellers"):
                
                @render_plotly
                def plot_top_sellers():
                    df = dat()
                    top_sales = df.groupby('product')['quantity_ordered'].sum().nlargest(input.n()).reset_index()
                    fig = px.bar(top_sales,
                                 x = 'product',
                                 y='quantity_ordered',
                                 color='quantity_ordered',
                                 color_continuous_scale='Blues')
                    fig = style_plotly_chart(fig,'Quantity Order')
                    return fig
                
            with ui.nav_panel("Top Sellers Value ($)"):
                
                @render_plotly
                def plot_top_sellers_value():
                    df = dat()
                    top_sales = df.groupby('product')['value'].sum().nlargest(input.n()).reset_index()
                    fig = px.bar(top_sales,
                                 x = 'product',
                                 y='value',
                                 color='value',
                                 color_continuous_scale='Blues')
                    fig = style_plotly_chart(fig,'Total Sales ($)')
                    return fig 
                
            with ui.nav_panel("Lowest Sellers"):
                
                @render_plotly
                def plot_lowest_sellers():
                    df = dat()
                    top_sales = df.groupby('product')['quantity_ordered'].sum().nsmallest(input.n()).reset_index()
                    fig = px.bar(top_sales,x = 'product',
                                 y='quantity_ordered',
                                 color='quantity_ordered',
                                 color_continuous_scale='Reds')
                    fig = style_plotly_chart(fig,'Quantity Order')
                    return fig 
                
            with ui.nav_panel("Lowest Sellers Value ($)"):
                
                @render_plotly
                def plot_lowest_sellers_value():
                    df = dat()
                    top_sales = df.groupby('product')['value'].sum().nsmallest(input.n()).reset_index()
                    fig = px.bar(top_sales,
                                 x = 'product',
                                 y='value',
                                 color='value',
                                 color_continuous_scale='Reds')
                    fig = style_plotly_chart(fig,'Total Sales ($)')
                    return fig 
    with ui.card():
        ui.card_header("Sales by Time of Day Heatmap")
        with ui.card_footer():
            ui.input_selectize(
                "day",
                "Select a Day:",
                [
                'Monday',
                'Tuesday', 
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday'],
                multiple=False,
                selected = "Monday"
            )

        
        @render.plot
        def plot_sales_by_time():
            df = dat()
            df_day = df[df['day'] == input.day()]
            sales_by_hour = df_day['hour'].value_counts().reindex(np.arange(0,24),fill_value=0)
            heatmap_data = sales_by_hour.values.reshape(24,1)
            sns.heatmap(heatmap_data,
                        annot=True,
                        fmt='d',
                        cmap='coolwarm',
                        cbar=False,
                        xticklabels=[],
                        yticklabels=[f"{i}:00" for i in range(24)])
            plt.xlabel("Order Count")
            plt.ylabel("Hour of Day")
             
        
with ui.card():
    ui.card_header("Sales by Location")
    @render.ui
    def plot_us_map():
        df = dat()
        
        with open('data/us-states.json', 'r') as usjson:
            us_states = json.load(usjson)
        
        df_states = df.groupby('state')['quantity_ordered'].sum().reset_index()
        
        df_cities = df.groupby('city').agg({'quantity_ordered':'sum','lat': 'mean', 'long': 'mean'}).reset_index()
        
        map = folium.Map(location=[37.0902, -95.7129],zoom_start=4)
        
        ## Adding markers to the cities
        
        for i in range(len(df_cities)):
            folium.Marker(
                location=[df_cities.iloc[i,2],df_cities.iloc[i,3]],
                tooltip=df_cities.iloc[i,0],
                popup=f"Total orders: {df_cities.iloc[i,1]}",
                icon=folium.Icon(color="blue")
            ).add_to(map)
        
        ## Adding Choropleth map of states
        
        folium.Choropleth(
            geo_data=us_states,
            data=df_states,
            columns=["state", "quantity_ordered"],
            key_on="feature.id",
            fill_color="YlOrRd",
            fill_opacity=0.8,
            line_opacity=0.3,
            nan_fill_color="white",
            legend_name="Total orders per state",
        ).add_to(map)  
        
        return map
        
    
    
