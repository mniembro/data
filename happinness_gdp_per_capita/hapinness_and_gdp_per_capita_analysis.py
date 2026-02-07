
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
# Plot UHC vs Cantril Score in 2021
# Get sorted list of unique regions
import matplotlib.cm as cm 
import matplotlib.colors as mcolors
import numpy

gdp_per_capita = pd.read_csv("gdp-per-capita-worldbank.csv")     # DGP per capita
happiness = pd.read_csv("happiness-cantril-ladder.csv")          # Happiness-cantril-ladder Score
healthcare = pd.read_csv("healthcare-access-quality-un.csv")     # UHC service coverage index 
expenditure = pd.read_csv("public-health-expenditure-share-gdp.csv") # Expenditure as % of the GDP
annual_expenditure_per_capita = pd.read_csv("annual-healthcare-expenditure-per-capita.csv")

continents= pd.read_csv("continents-according-to-our-world-in-data.csv") #list of countries per continent
continents=  continents.drop(["Year", "Entity"], axis=1)

# remove continents that do not have "Code" values (all codes have 3 characters)
continents = continents[continents["Code"].str.len() == 3]
healthcare = healthcare[healthcare["Code"].str.len() == 3]
gdp_per_capita = gdp_per_capita[gdp_per_capita["Code"].str.len() == 3]
expenditure = expenditure[expenditure["Code"].str.len() == 3]
# Rename
continents = continents.rename({"World regions according to OWID": "Region"}, axis=1)
# rename GDP per capita in $
gdp_per_capita = gdp_per_capita.rename({"GDP per capita, PPP (constant 2021 international $)": "GDP"}, axis=1)
annual_expenditure_per_capita = annual_expenditure_per_capita.rename({"Current health expenditure per capita, PPP (current international $)": "PPP"}, axis=1)
merged_gdp_health = pd.merge(gdp_per_capita, healthcare, on=["Code", "Year", "Entity"], how="inner")

merged_gdp_health = pd.merge(merged_gdp_health, continents, on=["Code"], how="inner")
annual_expenditure_per_capita = pd.merge(annual_expenditure_per_capita, continents, on=["Code"], how="inner")

merged_gdp_happiness_health = pd.merge(merged_gdp_health, happiness, on=["Code", "Year", "Entity"], how="inner")

# Filter for the year of interest
# The latest available year in the combined DataFrame is 2021
merged_gdp_happiness_health_2021 = merged_gdp_happiness_health[merged_gdp_happiness_health["Year"] == 2021]
annual_expenditure_per_capita_2021 = annual_expenditure_per_capita[annual_expenditure_per_capita["Year"]==2021]

merged_happiness_annual_expenditure = pd.merge(merged_gdp_happiness_health_2021, annual_expenditure_per_capita_2021, on=["Code", "Year", "Region", "Entity"], how="inner")

# add region and colour to expenditure
expenditure = pd.merge(expenditure, continents, on=["Code"], how="inner")
expenditure.to_csv("01_clean_expenditure_filtered.csv", index=False)
merged_happiness_annual_expenditure.to_csv("02_clean_happiness_annual_expenditure.csv")
all_merged_data = merged_happiness_annual_expenditure
happiness_df = merged_happiness_annual_expenditure
regions = sorted(merged_happiness_annual_expenditure["Region"].unique())
cantril_by_region = all_merged_data.groupby(["Region"])["Cantril ladder score"].mean().reset_index()
marker_per_region = {
    'Africa': 'o',
    'Asia': 's',
    'Europe': 'p',
    'North America': 'P',
    'Oceania': '*',
    'South America': 'D'
}

cmap = cm.viridis
norm = mcolors.Normalize(vmin=happiness_df['Cantril ladder score'].min(), vmax=happiness_df['Cantril ladder score'].max())


def create_scatter_plot_happiness_expenditure():

    plt.figure(figsize=(12, 8))

    ax = plt.gca()  # Get current axes

    def get_regional_avg(regional_merged_data):
        """function to get the average from dataframe"""
        uhc_avg = None
        ppp_avg = None
        cantril_avg = None
        all_cantril = []
        all_x = []
        all_y = []
        for _, row in regional_merged_data.iterrows():
            x = row["PPP"]
            y = row ["UHC service coverage index"]
            cantril = row["Cantril ladder score"]
            if numpy.isfinite(cantril):
                all_cantril.append(cantril)
            if numpy.isfinite(x) and numpy.isfinite(y):
                all_x.append(x)
                all_y.append(y)
        if all_cantril:
            cantril_avg = sum(all_cantril)/len(all_cantril)
        if all_x:
            ppp_avg = sum(all_x)/len(all_x)
        if all_y:
            uhc_avg = sum(all_y)/len(all_y)
        return cantril_avg, ppp_avg, uhc_avg
        

    region_handles = []
    text_handles = []
    our_countries = ["Brazil", "Canada", "Chile", "Mexico", "Romania"]

    # We'll store one mappable object to use for the colorbar
    mappable = None

    # graph per continent
    for region in regions:
        regional_merged_data = all_merged_data[all_merged_data["Region"] == region]

        colors = cmap(norm(regional_merged_data['Cantril ladder score']))
        entity = regional_merged_data["Entity"]
        
        happiness_rate = regional_merged_data['Entity']
        size =  regional_merged_data['Cantril ladder score']*15

        scatter = plt.scatter(
            regional_merged_data["PPP"],
            regional_merged_data["UHC service coverage index"],
            c=colors,
            marker=marker_per_region[region],
            s=size,
            label=entity,
            alpha=0.45,
            edgecolor='k'
        )

        # Create a dummy handle for the region legend
        region_handles.append(plt.Line2D([], [], color='gray', marker=marker_per_region[region],
                                        linestyle='None', label=region, markersize=10, markeredgecolor='k', alpha=0.5))
        # Save one of the scatter plots to use as the colorbar mappable
        if mappable is None:
            mappable = scatter

        # get the averages to do some comparisons with the data 
        cantril_avg, ppp_avg, uhc_avg = get_regional_avg(regional_merged_data)
        
        # adding some labels of countries we found interesting data from
        
        for _, row in regional_merged_data.iterrows():
            x = row["PPP"]
            y = row ["UHC service coverage index"]
            country = row["Entity"]
            cantril = row["Cantril ladder score"]
    
            if numpy.isfinite(x) and numpy.isfinite(y):
                offset = 140
                yoffset = offset/200
                # adjusting the states manually to be inside the figure
                if country=="United States":
                    offset = offset*-5
                    yoffset += 1
                # get countries with best/worst self-assessed well-being 
                if row["Cantril ladder score"]>7.5:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="g")
                if row["Cantril ladder score"]<3:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="b")
                # add the countries of the members of the team
                if country in our_countries:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="black")
                # countries that stand out due to being higher than avg 
                # adding multipliers so we show just the most extreme cases and avoid overlapping
                if x>ppp_avg*4:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="m")
                if y>uhc_avg*1.5:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="m")
                if cantril>cantril_avg*1.4:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="m")
                    
                # countries that stand out due to being lower than avg 

                if x*6<ppp_avg:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="tab:blue")
                if y*3<uhc_avg:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="tab:blue")
                if cantril*2.5<cantril_avg:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="tab:blue")
                # expenditure surprises 
                # not a lot of expending and very high well-being rate
                if x<5000 and cantril>7.1:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="tab:brown")
                # a lot of expending and less well-being 
                if x>7000 and cantril<6:
                    plt.text(x+offset, y-yoffset, country, fontsize=8, c="c")

    # Create a mappable object for the colorbar
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # required, even if empty

    # Add the colorbar
    cbar = plt.colorbar(sm, ax=ax, label="Cantril Ladder Score", alpha=.5)

    plt.xlabel("Current health expenditure per capita, PPP (current international $)")
    plt.ylabel("UHC service coverage index")
    plt.title("Happiness (Cantril Score) vs current health expenditure per capita. (Color = Score) in 2021")

    # markers per region legend
    region_legend = ax.legend(handles=region_handles, title="Region", loc="lower right", labelspacing=1)
    for text in region_legend.get_texts():
        text.set_size(8)
    ax.add_artist(region_legend)  


    countries_handles = {
        "our countries": "black", 
        "highest well-being rate (>.75)": "g", # green
        "lowest well-being rate (<.3)": "b", # blue 
        "countries that stand out (higher than avg)": "m", # magenta
        "countries that stand out (lower than avg)": "tab:blue",
        "low expenditure, higher well-being": "tab:brown",
        "high expenditure, lower happiness": "c" # removing because it was empty
    }
    # Create a dummy handle for the region legend
    for country, color in countries_handles.items():
        handle = plt.Line2D([], [], color=color, marker=">",
                        linestyle='None', label=country, markersize=10, markerfacecolor=color, markeredgecolor='b', alpha=0.5)
        text_handles.append(handle)

    #add legend of empty series
    countries_legend = plt.legend(handles=text_handles, title="", labelspacing=1.5, loc="lower right", frameon=True, borderpad=1.7,bbox_to_anchor=(0.82, 0.0))
    # Set legend label colors to match line colors
    for text, color in zip(countries_legend.get_texts(), countries_handles.values()):
        text.set_color(color)
        text.set_size(8)
    plt.tight_layout()
    plt.savefig("01_happiness_vs_UHC_service_coverage_and_health_exp_per_capita.png")
    plt.show()

def create_histogram():
    """function to create a histogram with the given parameters"""
    #histogram GDP expenditure per region
    expenditure_2021 = expenditure[expenditure["Year"] == 2021]
    mean_exp_GDP_by_region = expenditure_2021.groupby(["Region", "Year"])["Public health expenditure as a share of GDP"].mean().reset_index()


    # Create the bar plot with mapped colors
    fig, ax = plt.subplots(figsize=(8, 5))
    bar = ax.bar(
        mean_exp_GDP_by_region["Region"],
        mean_exp_GDP_by_region["Public health expenditure as a share of GDP"],
        color=cmap(norm(cantril_by_region['Cantril ladder score'])) ,edgecolor="black", alpha=.6
    )
    cantril_scores = []
    for cantril_score in cantril_by_region["Cantril ladder score"]:
        # add \n to continue in new line 
        score = " avg \ncantril score: \n{:.2f}".format(cantril_score)
        cantril_scores.append(score)

    ax.bar_label(bar, labels=cantril_scores, label_type='center', size=7)

    plt.title("Public Health Expenditure as % of GDP by Region (2021)")
    plt.ylabel("Expenditure (% of GDP)")

    # Create a mappable object for the colorbar
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # required, even if empty
    # Add the colorbar
    cbar = plt.colorbar(sm, ax=ax, label="Cantril Ladder Score", alpha=.5)

    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter()) 
    plt.xticks(rotation=45)
    plt.tight_layout()
    # add grid for reference 
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig("02_Histogram_Health_Expenditure_per_Region_2021.png")
    plt.show()


def create_bar_plot():
    """function to create a bar plot with the given parameters"""
    #GDP expenditure per Region

    # Create the bar plot with mapped colors
    fig, ax = plt.subplots(figsize=(8, 5))
    lines_per_region = {
        'Africa': '-',
        'Asia': '-',
        'Europe': '-',
        'North America': '--',
        'Oceania': '-',
        'South America': '-'
    }

    mean_exp_by_region_year = expenditure.groupby(["Region", "Year"])["Public health expenditure as a share of GDP"].mean().reset_index()
    mean_exp_by_region_1970 = mean_exp_by_region_year[mean_exp_by_region_year["Year"] > 1970]

    regions = mean_exp_by_region_year["Region"].unique()

    for region in sorted(regions):
        cantril = cantril_by_region[cantril_by_region["Region"]==region]
        region_df = mean_exp_by_region_1970[mean_exp_by_region_1970["Region"] == region].sort_values("Year")

        color =cmap(norm(cantril["Cantril ladder score"].iloc[0]))
        if region in ["South America"]:
            # add marker to one country to differentiate lines
            marker = marker_per_region[region]
        else:
            marker = ''
        hist = plt.plot(region_df["Year"], region_df["Public health expenditure as a share of GDP"], label=region, marker=marker, markersize=2, linestyle=lines_per_region[region], c=color)

    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # required, even if empty
    # Add the colorbar
    cbar = plt.colorbar(sm, ax=ax, label="Cantril Ladder Score", alpha=.5)

    plt.xlabel("Year")
    plt.ylabel("Expenditure (% of GDP)")
    plt.title("Public Health Expenditure as % of GDP by Region")
    plt.legend(title="Region")
    plt.grid(True)
    plt.tight_layout()
    # to display y-axis as percentages 
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter()) 
    plt.savefig("03_Health_Expenditure_per_Region.png")
    plt.show()

def create_scatter_plot():
    """function to create a scatter plot with the given parameters"""
    create_scatter_plot_happiness_expenditure()

def create_histogram():
    """function to create a histogram with the given parameters"""
    create_histogram()

def create_bar_plot():
    """function to create a bar plot with the given parameters"""
    create_bar_plot()