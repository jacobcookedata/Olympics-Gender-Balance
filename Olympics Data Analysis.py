#!/usr/bin/env python
# coding: utf-8

# # Olympics Results Data Analysis
# 
# Using SQLite queries within Python to analyse the gender balance of Olympic Games and the events held within them. This makes use of the pandasql package to run SQL queries on Pandas Dataframes, returning the result as another Dataframe. Visualisations and any further analysis are done within Python using tools such as Matplotlib and Seaborn.
# 
# ### There are several steps to my analysis:
# - Importing the packages required, and the data
# - Cleaning the data
# - Some exploratory visualisation and analysis
# - In depth analysis of gender participation balance

# ## Importing packages and data

# In[1]:


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#The package used to run sql queries on dataframes
from pandasql import sqldf
pysqldf = lambda q: sqldf(q, globals())


# In[2]:


regions = pd.read_csv(r"C:\Users\Jacob\Documents\Data Portfolios\Olympics\noc_regions.csv")
athletes = pd.read_csv(r"C:\Users\Jacob\Documents\Data Portfolios\Olympics\athlete_events.csv")

display(regions.head())
display(athletes.head())


# In[3]:


#Query which joins the two dataframes. 
#Since the two tables are relatively small, joining them fully in the first instance is most efficient.
#All of the columns are selected at this stage (without duplication).

q_join = """
    SELECT ID, Name, Sex, Age, Height, Weight, Team, Games, Year, Season, City, Sport, Event, Medal, regions.NOC, region as Region, Notes
    FROM athletes
    INNER JOIN regions
    ON athletes.NOC = regions.NOC
"""
df_join = pysqldf(q_join).set_index('ID')

df_join.head()


# ## Cleaning the data
# 
# I can drop any rows and columns which won't be used for the analysis. This might include any duplicated information.
# - The NOC, Region and Team all provide information on where the athlete is from or who they represent. Choose to keep the Region for this, instead of the Team. The Team always matches the Region in the recent games.
# - Can also drop the Notes column, which is not used for the analysis.
# - There is duplicated information across the Games, Year and Season columns. I could drop the Games column to prevent such duplication. I have chosen not to because it allows for the athletes to be grouped by the Games later. This is necessary (instead of grouping by Year) because Winter and Summer games weren't staggered to begin with.
# 
# 
# - There are also rows dropped corresponding to the sports no longer competed in. I have created a query that returns the last year in which a sport appears. The sports which last appear before 2008 are excluded. There are 15 sports which are removed, and they do not appear after 1950.

# In[56]:


#Dropping the team and notes columns
q_col_drop = """
    SELECT ID, Name, Sex, Age, Height, Weight, Games, Year, Season, City, Sport, Event, Medal, NOC, Region
    FROM df_join
"""

df_col_drop = pysqldf(q_col_drop).set_index('ID')

df_col_drop.head()


# In[57]:


#Query to identify the sports no longer competed in, and the year of their last inclusion.
q_last_inclusion = """
    SELECT Sport, MAX(Year) as Last_Inclusion
    FROM df_col_drop
    GROUP BY Sport
    HAVING Last_Inclusion < 2000
"""

df_last_inclusion = pysqldf(q_last_inclusion)
display(df_last_inclusion)



#Query to remove rows corresponding to the 15 old sports.
q_drop_sports = """
    SELECT *
    FROM df_col_drop
    WHERE Sport NOT IN ('Aeronautics', 'Alpinism', 'Art Competitions', 'Basque Pelota', 'Cricket', 'Croquet', 'Jeu De Paume', 'Lacrosse', 'Military Ski Patrol', 'Motorboating','Polo', 'Racquets', 'Roque', 'Rugby', 'Tug-Of-War')
"""

df_row_drop = pysqldf(q_drop_sports)


# ## Checking data quality
# Checking for NULL values, incorrect values and any inconsistencies. This will ensure I can do good analysis on the data and be confident in the results.

# In[58]:


#Any NULL values in my data?

#Some missing data: age, height, weight. Not currenlty using these columns, so ignore.
#Some null values are supposed to be: non-medallists
#Need to check that missing regions are okay.

df_row_drop.info()


# In[61]:


#Two groups: the Refugee Olympic Team; Tuvalu
#I think I can just replace the null values for these records.

display(regions[regions['region'].isnull()])

#No values of 'UNK' in the NOC column. These rows are all removed as athletes are competing in the old sports.
#display(df_row_drop[df_row_drop.Region.isnull()]) 


# In[8]:


#This query returns an error, since df_row_drop is not an SQL table
#Will have to perform the operation within Python.

q_replace_tuv = """
    UPDATE df_row_drop
    SET region = REPLACE(region, NULL, Tuvalu)
    WHERE NOC = 'TUV'
"""

#df_clean = pysqldf(q_replace_tuv)
#display(df_clean.head())


# In[9]:


#Using Python to insert the missing values.
df_row_drop.loc[df_row_drop['NOC'] == 'TUV', ['Region']] = 'Tuvalu'
df_row_drop.loc[df_row_drop['NOC'] == 'ROT', ['Region']] = 'Refugee Olympic Team'


# In[10]:


#When investigating medals available by gender, the nulls in the medal column made joins impossible.
#Will replace them with a string.

df_row_drop['Medal'].fillna('None', inplace=True)

df_row_drop.info()


# In[11]:


#Dataframe to be taken forward for analysis.
df_eda = df_row_drop.copy()
df_eda


# # Initial Exploration
# - Check all columns. Are the values likely?
# - Plot distibutions of numerical columns.

# In[12]:


#Checking the Sex column

q_sex_check = """
    SELECT Sex, COUNT(*) as Count
    FROM df_eda
    GROUP BY Sex
"""

df_sex = pysqldf(q_sex_check)
df_sex


# In[13]:


#Checking the Age column

q_age_check = """
    SELECT Age, COUNT(*) as Count
    FROM df_eda
    GROUP BY Age
"""

df_age = pysqldf(q_age_check)

display(df_age) #Reveals 8807 missing values.

df_age[df_age['Age']!='NA'].plot(kind='scatter', x='Age', y='Count')
plt.title('Distribution of the age of athletes at all Olympic Games');

#A roughly normal distribution. There is a skew towards the higher ages.


# In[14]:


#Checking the Height column

q_height_check = """
    SELECT Height, COUNT(*) as Count
    FROM df_eda
    GROUP BY Height
"""

df_height = pysqldf(q_height_check)

display(df_height) #Reveals 56036 missing values.

print(df_height['Height'].unique()) #All integer values.

df_height[df_height['Height']!='NA'].plot(kind='scatter', x='Height', y='Count') #Not enough data to be normal?
plt.title('Height distribution of Olympic athletes'); 


# In[15]:


#Is it possible that the distribution would be different if plotted by gender?

q_height_gender = """
    SELECT Height, Sex, COUNT(*) as Count
    FROM df_eda
    GROUP BY Height, Sex
"""

df_height_gender = pysqldf(q_height_gender)

df_height_gender

sns.scatterplot(data=df_height_gender[df_height_gender['Height']!='NA'], x='Height', y='Count', hue='Sex')
plt.title('Height distribution by gender');


# In[16]:


#Checking the Weight column

q_weight_gender = """
    SELECT Weight, Sex, COUNT(*) as Count
    FROM df_eda
    GROUP BY Weight, Sex
"""

df_weight_gender = pysqldf(q_weight_gender)

display(df_weight_gender) #Reveals 58726 missing values.

#print(df_weight_gender['Weight'].unique()) #Reveals lots of decimal values. Do these warrant changing?

sns.scatterplot(data=df_weight_gender[df_weight_gender['Weight']!='NA'], x='Weight', y='Count', hue='Sex') #Not enough data to be normal?
plt.title('Weight distribution by gender');


# In[17]:


#Can I alter the query to round the weight values?

q_weight_correct = """
    SELECT Weight, Sex, COUNT(*) as Count
    FROM (
        SELECT Sex, ROUND(Weight) as Weight
        FROM df_eda
    )
    GROUP BY Weight, Sex
"""

df_weight_correct = pysqldf(q_weight_correct)

display(df_weight_correct)

#print(df_weight_correct['Weight'].unique())

sns.scatterplot(data=df_weight_correct[df_weight_correct['Weight']!='NA'], x='Weight', y='Count', hue='Sex')
plt.title('Weight distribution by gender - rounded');


# In[18]:


#Checking the Team column


#Note that the athletes dataframe has been queried, since the team column has been removed from the working dataframe.
q_team_check = """
    SELECT Team, COUNT(*) as Count
    FROM athletes
    GROUP BY Team
    ORDER BY Count DESC
"""

df_team_check = pysqldf(q_team_check)

display(df_team_check) #Some messy data!

#Probably messy due to the earlier olympics events.
#More recently, the team and country has aligned more closely.
#Might just have to remove this column - nothing meaningful to be gained from >1000 team names.


# In[19]:


#Checking the NOC column

q_noc_check = """
    SELECT NOC, COUNT(*) as Count
    FROM df_eda
    GROUP BY NOC
    --ORDER BY Count DESC
"""

df_noc_check = pysqldf(q_noc_check)

display(df_noc_check) #Nothing to mention here.


# In[20]:


#Checking the Year column

q_year_check = """
    SELECT Year, COUNT(*) as Count
    FROM df_eda
    GROUP BY Year
    --ORDER BY Count DESC
"""

df_year_check = pysqldf(q_year_check)

display(df_year_check.head()) #Nothing to mention here.

df_year_check.plot(kind='scatter', x='Year', y='Count')
plt.title('Number of athletes competing in each year');

#Notice a change in trend when summer and winter olympics run 2 years apart from 1994.


# In[21]:


#Split based on summer/winter

q_year_split = """
    SELECT Year, Season, COUNT(*) as Count
    FROM df_eda
    GROUP BY Year, Season
    --ORDER BY Count DESC
"""

df_year_split = pysqldf(q_year_split)

sns.scatterplot(data=df_year_split, x='Year', y='Count', hue='Season')
plt.title('Number of athletes competing in each Games');

#Appears that 1932 summer olympics had decreased participation. Great Depression?


# In[22]:


#Checking the Season column

q_season_check = """
    SELECT Season, COUNT(*) as Count
    FROM df_eda
    GROUP BY Season
    --ORDER BY Count DESC
"""

df_season_check = pysqldf(q_season_check)

display(df_season_check) #Nothing to mention here.


# In[23]:


#Checking the City column

q_city_check = """
    SELECT City, COUNT(*) as Count
    FROM df_eda
    GROUP BY City
    --ORDER BY Count DESC
"""

df_city_check = pysqldf(q_city_check)

display(df_city_check.head()) #Nothing to mention here.


# In[24]:


#Checking the Sport column

q_sport_check = """
    SELECT Sport, COUNT(*) as Count
    FROM df_eda
    GROUP BY Sport
    ORDER BY Count DESC
"""

df_sport_check = pysqldf(q_sport_check)

display(df_sport_check)

#print(df_sport_check.Sport.unique())

#The 15 excluded events do not appear.


# In[25]:


#Checking the Event column

q_event_check = """
    SELECT Event, COUNT(*) as Count
    FROM df_eda
    GROUP BY Event
    ORDER BY Count DESC
"""

df_event_check = pysqldf(q_event_check)

display(df_event_check) #Not very revealing - very large number of events.

#Note that the events each appear to have the sport at the beginning of their name. Could remove.


# In[26]:


#Checking the Medal column

q_medal_check = """
    SELECT Medal, COUNT(*) as Count
    FROM df_eda
    GROUP BY Medal
    --ORDER BY Count DESC
"""

df_medal_check = pysqldf(q_medal_check)

display(df_medal_check)

#Unequal numbers!
#Are there events that awarded two bronze medals?
#Events with only a gold medal?


# # Plan for further investigation: Gender equality
# 
# Questions
# - How has male/female participation as a whole changed over time?
# - What are the sports and events with best/worst gender equality?
# - Are there any obvious areas for improved participation?
# 
# Hypotheses
# - Women can participate in less events than men.
# - Women have fewer places made available within the Olympic events.
# - Olympic Games are becoming more equal over time.
# 
# Plan of action
# - Further investigate the male/female split across games and sports.
# - Develop a method of quantifying the level of equality.
# - Looking at access to number of events; participation within the events.

# # Equality within games as a whole

# In[27]:


q_summer_equality = """
    SELECT Year, Sex, COUNT(*) as Num_Athletes
    FROM df_eda
    WHERE Season = 'Summer'
    GROUP BY Year, Sex
"""

df_summer_equality = pysqldf(q_summer_equality)
#display(df_summer_equality)

sns.scatterplot(data=df_summer_equality, x='Year', y='Num_Athletes', hue='Sex')
plt.title('Participation by gender at the Summer Olympics')
plt.ylabel('Number of Athletes');


# - Above plot reveals that women have been under-represented at every summer games.
# - No women at the first modern Olympic games.
# - Gap closing consistently over time.

# In[28]:


q_winter_equality = """
    SELECT Year, Sex, COUNT(*) as Num_Athletes
    FROM df_eda
    WHERE Season = 'Winter'
    GROUP BY Year, Sex
"""

df_winter_equality = pysqldf(q_winter_equality)
#display(df_winter_equality)

sns.scatterplot(data=df_winter_equality, x='Year', y='Num_Athletes', hue='Sex')
plt.title('Participation by gender at the Winter Olympics')
plt.ylabel('Number of Athletes');


# - Similar story to summer olympics.
# - Both male and female participation increasing at similar rates in winter olympics.

# In[29]:


#A participation ratio might be calculated?

q_sum_equality_ratio = """
    SELECT 
        male.Year      as Year
        , male.Num_M   as Men
        , female.Num_F as Women
    FROM
        (SELECT Year, COUNT(*) as Num_M
        FROM df_eda
        WHERE Season='Summer' AND Sex='M'
        GROUP BY Year) male
    LEFT JOIN
        (SELECT Year, COUNT(*) as Num_F
        FROM df_eda
        WHERE Season='Summer' AND Sex='F'
        GROUP BY Year) female
    ON
        male.year = female.year
"""

df_sum_equality_ratio = pysqldf(q_sum_equality_ratio)

#The calculation of the ratio
df_sum_equality_ratio.fillna(0, inplace=True)
df_sum_equality_ratio['Ratio'] = df_sum_equality_ratio['Men']/(df_sum_equality_ratio['Men']+df_sum_equality_ratio['Women'])

#Plotting to revela the trend
df_sum_equality_ratio.plot(kind='scatter', x='Year', y='Ratio')
plt.title('Proportion of men at each summer olympics')
plt.ylabel('Proportion of men');

#display(df_sum_equality_ratio)


# In[30]:


#Same again for the winter olympics
q_win_equality_ratio = """
    SELECT 
        male.Year      as Year
        , male.Num_M   as Men
        , female.Num_F as Women
    FROM
        (SELECT Year, COUNT(*) as Num_M
        FROM df_eda
        WHERE Season='Winter' AND Sex='M'
        GROUP BY Year) male
    LEFT JOIN
        (SELECT Year, COUNT(*) as Num_F
        FROM df_eda
        WHERE Season='Winter' AND Sex='F'
        GROUP BY Year) female
    ON
        male.year = female.year
"""

df_win_equality_ratio = pysqldf(q_win_equality_ratio)

#The calculation of the ratio
df_win_equality_ratio.fillna(0, inplace=True)
df_win_equality_ratio['Ratio'] = df_win_equality_ratio['Men']/(df_win_equality_ratio['Men']+df_win_equality_ratio['Women'])

#Plotting to revela the trend
df_win_equality_ratio.plot(kind='scatter', x='Year', y='Ratio')
plt.title('Proportion of men at each winter olympics')
plt.ylabel('Proportion of men');

#display(df_win_equality_ratio)


# - Both the summer and winter games have been moving towards equal numbers of men and women competing over time.
# - Summer olympics has got closer to equality, reaching a 55-45 split in the most recent games.
# - Winter olympics a touch further away, reaching a 58-42 split in 2014. Actually worsened somewhat for the 2018 games.
# - The two most recent games are pretty similar for both summer and winter. To investigate the sports I will use both of these games to begin with.

# # Equality with summer sports

# In[31]:


#Gender breakdown by games and sport
#Each subquery counts number of participants of a certain gender in each sport for a specific games.
#Joins on the four subqueries to allow the four counts to be palced in a table.
q_sport_equality_sum_recent = """
    SELECT 
        F_2016.Sport
        , F_2012.F2012
        , M_2012.M2012
        , F_2016.F2016
        , M_2016.M2016
    FROM
        (SELECT Sport, COUNT(*) AS F2016
        FROM df_eda
        WHERE Year='2016' AND Sex='F'
        GROUP BY Sport) F_2016
    LEFT JOIN
        (SELECT Sport, COUNT(*) AS M2012
        FROM df_eda
        WHERE Year='2012' AND Sex='M'
        GROUP BY Sport) M_2012
    ON
        F_2016.Sport = M_2012.Sport
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS M2016
        FROM df_eda
        WHERE Year='2016' AND Sex='M'
        GROUP BY Sport) M_2016
    ON
        F_2016.Sport = M_2016.Sport
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS F2012
        FROM df_eda
        WHERE Year='2012' AND Sex='F'
        GROUP BY Sport) F_2012
    ON
        F_2012.Sport = F_2016.Sport
"""

df_sport_equality_sum_recent = pysqldf(q_sport_equality_sum_recent)


# In[32]:


#Equality ratios calculated for each sport.
df_sport_equality_sum_recent.fillna(0, inplace=True) #Allows ratios to be calculated where there is no participation.

df_sport_equality_sum_recent['ratio_2012'] = df_sport_equality_sum_recent['M2012']/(df_sport_equality_sum_recent['M2012']+df_sport_equality_sum_recent['F2012'])
df_sport_equality_sum_recent['ratio_2016'] = df_sport_equality_sum_recent['M2016']/(df_sport_equality_sum_recent['M2016']+df_sport_equality_sum_recent['F2016'])

df_sport_equality_sum_recent['ratio_joint'] = (df_sport_equality_sum_recent['M2016']+df_sport_equality_sum_recent['M2012'])/(df_sport_equality_sum_recent['M2016']+df_sport_equality_sum_recent['F2016']+df_sport_equality_sum_recent['M2012']+df_sport_equality_sum_recent['F2012'])

df_sport_equality_sum_recent.head()


# In[33]:


from bokeh.plotting import Figure, output_notebook, show, save
from bokeh.models import ColumnDataSource, HoverTool, GroupFilter, CDSView

output_notebook()


# In[34]:


#Trying a Bokeh plot!

data = ColumnDataSource(df_sport_equality_sum_recent)
summer_sports = Figure(tooltips=[('Sport', '@Sport'), ('Gender Ratio', '@ratio_joint')], width=300, height=300)

summer_sports.scatter(source=data, x='ratio_2012', y='ratio_2016', size=8)

show(summer_sports);


# - Cluster of sport close to equality.
# - Still lots that favour male participation.
# - Boxing and wrestling heavily male dominated.
# - Rhythmic gymnastics and synch swimming are female-only

# # Winter Sports Equality

# In[35]:


#Gender breakdown by games and sport
q_sport_equality_wint_recent = """
    SELECT 
        F_2014.Sport
        , F_2014.F2014
        , M_2014.M2014
        , F_2010.F2010
        , M_2010.M2010
    FROM
        (SELECT Sport, COUNT(*) AS M2014
        FROM df_eda
        WHERE Year='2014' AND Sex='M'
        GROUP BY Sport) M_2014
    LEFT JOIN
        (SELECT Sport, COUNT(*) AS F2014
        FROM df_eda
        WHERE Year='2014' AND Sex='F'
        GROUP BY Sport) F_2014
    ON
        F_2014.Sport = M_2014.Sport
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS M2010
        FROM df_eda
        WHERE Year='2010' AND Sex='M'
        GROUP BY Sport) M_2010
    ON
        M_2014.Sport = M_2010.Sport
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS F2010
        FROM df_eda
        WHERE Year='2010' AND Sex='F'
        GROUP BY Sport) F_2010
    ON
        M_2014.Sport = F_2010.Sport
"""

df_sport_equality_wint_recent = pysqldf(q_sport_equality_wint_recent)


# In[36]:


df_sport_equality_wint_recent.fillna(0, inplace=True)

df_sport_equality_wint_recent['ratio_2014'] = df_sport_equality_wint_recent['M2014']/(df_sport_equality_wint_recent['M2014']+df_sport_equality_wint_recent['F2014'])
df_sport_equality_wint_recent['ratio_2010'] = df_sport_equality_wint_recent['M2010']/(df_sport_equality_wint_recent['M2010']+df_sport_equality_wint_recent['F2010'])

df_sport_equality_wint_recent['ratio_joint'] = (df_sport_equality_wint_recent['M2010']+df_sport_equality_wint_recent['M2014'])/(df_sport_equality_wint_recent['M2010']+df_sport_equality_wint_recent['F2010']+df_sport_equality_wint_recent['M2014']+df_sport_equality_wint_recent['F2014'])

df_sport_equality_wint_recent


# In[37]:


data = ColumnDataSource(df_sport_equality_wint_recent)
winter_sports = Figure(tooltips=[('Sport', '@Sport'), ('Gender Ratio', '@ratio_joint')], width=300, height=300)

winter_sports.scatter(source=data, x='ratio_2010', y='ratio_2014', size=8)

show(winter_sports);


# - Some sports are far from gender equality (bobsleigh, luge, ice hockey)
# - Some sports are close to equality (figure skating, speed skating, curling)
# - Never any sports with gender ratios much below 0.5.
# - Nordic combined male-only
# - Ski jumping was male only in 2010

# # One-gender sports?
# - Due to the use of inner joins on my subqueries, I have excluded any sports which do not appear in all of them.
# - They could be only male, or only female.
# - Also might only appear in one of the two games.
# - The queries above have been altered to include the findings below.

# In[38]:


#Full outser joins unavailble, so using individual left joins to check for missing sports.
#One example below: takes all sports from 2016 to reveal which ones are added compared to 2012.
#Gender comparisons also made by switching the order of male/female subqueries to reveal single-gender sports.

q_sum_games_compare = """
    SELECT 
        g2016.Sport, C2012, C2016
    FROM
        (SELECT Sport, COUNT(*) AS C2016
        FROM df_eda
        WHERE Year='2016'
        GROUP BY Sport) g2016
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS C2012
        FROM df_eda
        WHERE Year='2012'
        GROUP BY Sport) g2012
    ON
        g2012.Sport = g2016.Sport
"""

df_sum_games_compare = pysqldf(q_sum_games_compare)

#df_sum_games_compare


# - 2012 and 2016 games: rhythmic gymnastics and synchronized swimming are female only; no male only sports.
# - 2012: All sports taken forward to 2016
# - 2016 only sports: golf and rugby sevens added
# - Can alter the summer games query to have left joins, and start with F2016.

# In[39]:


#Example of left join to compare sports by gender. 
#This query would reveal any female-only sports in 2010.
q_wint_games_compare = """
    SELECT 
        F_2010.Sport
        , F_2010.F2010
        , M_2010.M2010
    FROM
        (SELECT Sport, COUNT(*) AS F2010
        FROM df_eda
        WHERE Year='2010' AND Sex='F'
        GROUP BY Sport) F_2010
    LEFT JOIN 
        (SELECT Sport, COUNT(*) AS M2010
        FROM df_eda
        WHERE Year='2010' AND Sex='M'
        GROUP BY Sport) M_2010
    ON
        F_2010.Sport = M_2010.Sport
"""

df_wint_games_compare = pysqldf(q_wint_games_compare)

#df_wint_games_compare


# - 2014: no female only; Nordic combined is male only
# - 2010: Nordic combined and ski jumping male only; no female only
# - No change in available sports.
# - If the winter games query begins with one of the male queries and uses left joins, all sports will be included.

# # What about number medals available?
# - Some sports have differing participation by gender.
# - Does this translate to medal winning opportunities?
# - Are there just smaller fields competing for each medal in some sports?

# In[40]:


#To make the non-medallists a category, the null values in the medal column had to be replaced.
#This operation is completed in the null values section.


q_sum2012_sport_medals = """
    SELECT
        F_medals.Sport
        , F_medals.Medal
        , F_medals
        , M_medals
    FROM
        (SELECT Sport, Medal, COUNT(*) as F_Medals
        FROM df_eda
        WHERE Year='2012' AND Sex='F'
        GROUP BY Sport, Medal) F_medals
    LEFT JOIN
        (SELECT Sport, Medal, COUNT(*) as M_Medals
        FROM df_eda
        WHERE Year='2012' AND Sex='M'
        GROUP BY Sport, Medal) M_medals
    ON
        F_medals.Sport=M_medals.Sport
    AND
        F_medals.Medal=M_medals.Medal
"""

df_sum2012_sport_medals = pysqldf(q_sum2012_sport_medals)

df_sum2012_sport_medals.fillna(0, inplace=True)

df_sum2012_sport_medals


# In[41]:


from bokeh.models.widgets import Tabs, Panel

data_none = ColumnDataSource(df_sum2012_sport_medals[df_sum2012_sport_medals['Medal']=='None'])
none_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
none_scatter.scatter(source=data_none, x='F_Medals', y='M_Medals', size=8)

data_golds = ColumnDataSource(df_sum2012_sport_medals[df_sum2012_sport_medals['Medal']=='Gold'])
golds_scatter = Figure(title='Number of golds per summer sport', x_axis_label='Golds for women', y_axis_label='Golds for men', tooltips=[('Sport', '@Sport')], width=400, height=300)
golds_scatter.scatter(source=data_golds, x='F_Medals', y='M_Medals', size=8)


data_silvers = ColumnDataSource(df_sum2012_sport_medals[df_sum2012_sport_medals['Medal']=='Silver'])
silvers_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
silvers_scatter.scatter(source=data_silvers, x='F_Medals', y='M_Medals', size=8)

data_bronzes = ColumnDataSource(df_sum2012_sport_medals[df_sum2012_sport_medals['Medal']=='Bronze'])
bronzes_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
bronzes_scatter.scatter(source=data_bronzes, x='F_Medals', y='M_Medals', size=8)

none_panel = Panel(child=none_scatter, title='Non-Medallists')
gold_panel = Panel(child=golds_scatter, title='Gold Medallists')
silver_panel = Panel(child=silvers_scatter, title='Silver Medallists')
bronze_panel = Panel(child=bronzes_scatter, title='Bronze Medallists')

all_medals = Tabs(tabs=[none_panel, gold_panel, silver_panel, bronze_panel])
show(all_medals)


# In[42]:


data = ColumnDataSource(df_sum2012_sport_medals)

medals_scatter = Figure(title='Number of events per summer sport', tooltips=[('Sport', '@Sport')], width=400, height=300)
medals_scatter.scatter(source=data, x='F_Medals', y='M_Medals', size=8)

show(medals_scatter)


# In[43]:


#Not sure if team events cause multiple counts of the number of gold medals.
#Counting unique events might be a better measure.

q_sum2012_sport_events = """
    SELECT
        F.Sport
        , F_events
        , M_events
    FROM
        (SELECT Sport, COUNT(DISTINCT(Event)) as F_events
        FROM df_eda
        WHERE Year='2012' AND Sex='F'
        GROUP BY Sport) F
    LEFT JOIN
        (SELECT Sport, COUNT(DISTINCT(Event)) as M_events
        FROM df_eda
        WHERE Year='2012' AND Sex='M'
        GROUP BY Sport) M
    ON
        F.Sport=M.Sport

"""

df_sum2012_sport_events = pysqldf(q_sum2012_sport_events)

df_sum2012_sport_events.fillna(0, inplace=True)


# In[44]:


data = ColumnDataSource(df_sum2012_sport_events)

events_scatter = Figure(title='Number of events per summer sport', x_axis_label='Events for women', y_axis_label='Events for men',tooltips=[('Sport', '@Sport')], width=400, height=300)
events_scatter.scatter(source=data, x='F_events', y='M_events', size=8)

show(events_scatter)


# In[45]:


q_wint2014_sport_medals = """
    SELECT
        F_medals.Sport
        , F_medals.Medal
        , F_medals
        , M_medals
    FROM
        (SELECT Sport, Medal, COUNT(*) as F_Medals
        FROM df_eda
        WHERE Year='2014' AND Sex='F'
        GROUP BY Sport, Medal) F_medals
    LEFT JOIN
        (SELECT Sport, Medal, COUNT(*) as M_Medals
        FROM df_eda
        WHERE Year='2014' AND Sex='M'
        GROUP BY Sport, Medal) M_medals
    ON
        F_medals.Sport=M_medals.Sport
    AND
        F_medals.Medal=M_medals.Medal
"""

df_wint2014_sport_medals = pysqldf(q_wint2014_sport_medals)

df_wint2014_sport_medals.fillna(0, inplace=True)


# In[46]:


data_none = ColumnDataSource(df_wint2014_sport_medals[df_wint2014_sport_medals['Medal']=='None'])
none_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
none_scatter.scatter(source=data_none, x='F_Medals', y='M_Medals', size=8)

data_golds = ColumnDataSource(df_wint2014_sport_medals[df_wint2014_sport_medals['Medal']=='Gold'])
golds_scatter = Figure(title='Number of golds per winter sport', x_axis_label='Golds for women', y_axis_label='Golds for men',tooltips=[('Sport', '@Sport')], width=400, height=300)
golds_scatter.scatter(source=data_golds, x='F_Medals', y='M_Medals', size=8)

data_silvers = ColumnDataSource(df_wint2014_sport_medals[df_wint2014_sport_medals['Medal']=='Silver'])
silvers_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
silvers_scatter.scatter(source=data_silvers, x='F_Medals', y='M_Medals', size=8)

data_bronzes = ColumnDataSource(df_wint2014_sport_medals[df_wint2014_sport_medals['Medal']=='Bronze'])
bronzes_scatter = Figure(tooltips=[('Sport', '@Sport')], width=400, height=300)
bronzes_scatter.scatter(source=data_bronzes, x='F_Medals', y='M_Medals', size=8)

none_panel = Panel(child=none_scatter, title='Non-Medallists')
gold_panel = Panel(child=golds_scatter, title='Gold Medallists')
silver_panel = Panel(child=silvers_scatter, title='Silver Medallists')
bronze_panel = Panel(child=bronzes_scatter, title='Bronze Medallists')

all_medals = Tabs(tabs=[none_panel, gold_panel, silver_panel, bronze_panel])
show(all_medals)


# In[47]:


q_wint2014_sport_events = """
    SELECT
        F.Sport
        , F_events
        , M_events
    FROM
        (SELECT Sport, COUNT(DISTINCT(Event)) as F_events
        FROM df_eda
        WHERE Year='2014' AND Sex='F'
        GROUP BY Sport) F
    LEFT JOIN
        (SELECT Sport, COUNT(DISTINCT(Event)) as M_events
        FROM df_eda
        WHERE Year='2014' AND Sex='M'
        GROUP BY Sport) M
    ON
        F.Sport=M.Sport

"""

df_wint2014_sport_events = pysqldf(q_wint2014_sport_events)

df_wint2014_sport_events.fillna(0, inplace=True)


# In[48]:


data = ColumnDataSource(df_wint2014_sport_events)

events_scatter = Figure(title='Number of events per winter sport', x_axis_label='Events for women', y_axis_label='Events for men',tooltips=[('Sport', '@Sport')], width=400, height=300)
events_scatter.scatter(source=data, x='F_events', y='M_events', size=8)

show(events_scatter)


# # Looking for correlations, metrics
# - Could investigate whether increased gender equality in games leads to success for nations.
# - Metric for nations' gender equality over time.
# - Metric for the success of nations over time.
# - Correlation between the two metrics?

# In[49]:


#Creating a total medal table can act as the basis for a measure of success.
q_total_medal_table = """
    SELECT
        regions.Region
        , gold.Golds
        , silver.Silvers
        , bronze.Bronzes
    FROM
        (SELECT DISTINCT(Region) as Region
        FROM df_eda) regions
    LEFT JOIN
        (SELECT Region, COUNT(*) as Golds
        FROM df_eda
        WHERE Medal = 'Gold'
        GROUP BY Region) gold
    ON 
        regions.Region = gold.Region
    LEFT JOIN
        (SELECT Region, COUNT(*) as Silvers
        FROM df_eda
        WHERE Medal = 'Silver'
        GROUP BY Region) silver
    ON
        regions.Region = silver.Region
    LEFT JOIN
        (SELECT Region, COUNT(*) as Bronzes
        FROM df_eda
        WHERE Medal = 'Bronze'
        GROUP BY Region) bronze
    ON
        regions.Region = bronze.Region
    ORDER BY Golds DESC    
    
"""

df_table = pysqldf(q_total_medal_table)
df_table


# In[50]:


#What about measuring equality for nations over time?
#Aiming to calculate proportion of genders at each games for each nation.


q_nation_equality = """
    SELECT 
        games.Games
        , games.Year
        , games.Season
        , regions.Region
        , men.Men
        , women.Women
        , medals.Medals
    FROM
        (SELECT DISTINCT(Games), Year, Season
        FROM df_eda) games
    CROSS JOIN
        (SELECT DISTINCT(Region)
        FROM df_eda) regions
        
    LEFT JOIN
        (SELECT Games, Region, COUNT(*) as Men
        FROM df_eda
        WHERE Sex = 'M'
        GROUP BY Games, Region) men
    ON
        games.Games = men.Games
    AND
        regions.Region = men.Region
        
    LEFT JOIN
        (SELECT Games, Region, COUNT(*) as Women
        FROM df_eda
        WHERE Sex = 'F'
        GROUP BY Games, Region) women
    ON
        games.Games = women.Games
    AND
        regions.Region = women.Region
        
    LEFT JOIN
        (SELECT Games, Region, COUNT(*) as Medals
        FROM df_eda
        WHERE Medal IN ('Gold', 'Silver', 'Bronze')
        GROUP BY Games, Region) medals
    ON
        games.Games = medals.Games
    AND
        regions.Region = medals.Region
        
"""

df_nation_equality = pysqldf(q_nation_equality)

df_nation_equality_calc = df_nation_equality.copy()

df_nation_equality_calc.dropna(thresh=3, inplace=True) #Removes rows where a nation has no participation in a Games.
df_nation_equality_calc.fillna(0, inplace=True)
df_nation_equality_calc['Gender_Ratio'] = df_nation_equality_calc['Men']/(df_nation_equality_calc['Men']+df_nation_equality_calc['Women'])
df_nation_equality_calc['Medals_Per_Athlete'] = df_nation_equality_calc['Medals']/(df_nation_equality_calc['Men']+df_nation_equality_calc['Women'])


df_nation_equality_calc.select_dtypes('number').corr() #Doesn't show strong relationships.

#Gender ratio has almost no impact on number of medals won by countries.
#Number of men and women both have strong positive correlation with number of medals won.
#The year has the strongest correlation with the gender ratio.


# In[51]:


q_grouped_equality = """
    SELECT 
        Region
        , SUM(Men) as Men
        , SUM(Women) as Women
        , SUM(Medals) as Medals
    FROM 
        df_nation_equality_calc
    WHERE Season = 'Winter'
    GROUP BY Region
    ORDER BY Medals DESC
"""

df_grouped_equality = pysqldf(q_grouped_equality)

df_grouped_equality['Gender_Ratio'] = df_grouped_equality['Men']/(df_grouped_equality['Men']+df_grouped_equality['Women'])
df_grouped_equality['Medals_Per_Athlete'] = df_grouped_equality['Medals']/(df_grouped_equality['Men']+df_grouped_equality['Women'])

df_grouped_equality.select_dtypes('number').corr()


# - Correlations found in the data, and what has been learned.
# Explored the correlations between the ratio of men and women in nation's teams at each of the games and varibales such as the year, the number of medals, and the number of medals per athlete. I found the number of medals won by teams to be strongly correlated with the number of athletes within the team. This suggests that nations with larger populations and increased sporting budgets are more successful at the Olympics. However, I did not find the gender ratio to be strongly correlated with any variables except the year. This reaffirms that the Olympics have become more equal over time, but suggests that a gender equal team does not necessarily lead to greater success. There is a weak correlation that suggests that greater gender equality increases the number of medals won, but this is a far weaker one than the number of athletes.
# 
# - New connections and relationships
# Creating a table which shows the number of medals won and the gender equality for each team at every games has revealed the possibility of tracking the progress of nations towards gender equality. I could perform analyses to reveal the teams which most need to address the imbalance of male and female participants. Any countires which consistently have a deficit in one gender could be looked at.
# Since the gender equality metric is not correlated strongly with the success of teams, perhaps I could investigate some other variable to find a driver of success. I already know that having as many athletes as possible is important. Perhaps I couold find some funding information from elsewhere. The age, height, and weight could be looked at.
# 
# 
# - New metrics
# I have created a medal table calculator in order to explore the effect of gender equality on the number of medals won. I began by cross joining the distinct values in the Games column with those in the Region column. This created a record for every nation at every games. Left joins were then used to populate the table with the number of men, women, and medals won at each of the games for each of the nations. The resulting table could be aggregated by Region in order to calculate a total medal table for all games. Further selections can be made before the aggregation to reveal a winter/summer total medal table, for example.
