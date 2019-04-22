# -*- coding: utf-8 -*-
"""
Created on Sun Apr 21 22:05:47 2019

@author: Jacob
"""
import urllib.request
import zipfile
import os
import shutil
import time
from census import Census
import pickle
import geopandas as gpd
from scripts import counties_from_block_groups
#%%
# source: http://code.activestate.com/recipes/577775-state-fips-codes-dict/
FIPS = {
    'WA': '53', 'DE': '10', 'DC': '11', 'WI': '55', 'WV': '54', 'HI': '15',
    'FL': '12', 'WY': '56', 'NJ': '34', 'NM': '35', 'TX': '48',
    'LA': '22', 'NC': '37', 'ND': '38', 'NE': '31', 'TN': '47', 'NY': '36',
    'PA': '42', 'AK': '02', 'NV': '32', 'NH': '33', 'VA': '51', 'CO': '08',
    'CA': '06', 'AL': '01', 'AR': '05', 'VT': '50', 'IL': '17', 'GA': '13',
    'IN': '18', 'IA': '19', 'MA': '25', 'AZ': '04', 'ID': '16', 'CT': '09',
    'ME': '23', 'MD': '24', 'OK': '40', 'OH': '39', 'UT': '49', 'MO': '29',
    'MN': '27', 'MI': '26', 
    'RI': '44', 'KS': '20', 'MT': '30', 'MS': '28',
    'SC': '45', 'KY': '21', 'OR': '41', 'SD': '46'
}
#%%

def download_files(states, output_path, description):
    ''' Downloads block files from US census website
    
    Arguments: 
        states: dictionary of states and corresponding URLs
        output_path: path to directory for state output folders, includes year
        description: what we are downloading, with a / at the start
            (example: /cblocks)
    '''   
    start_time = time.time()
    # download files
    for st in states:
        
        # download
        if not os.path.isdir(output_path + st):
            os.mkdir(output_path + st)
        file_loc = output_path + st + '/temp.zip'
        
        try:
            urllib.request.urlretrieve(states[st], file_loc)
        
            # unzip
            zip_ref = zipfile.ZipFile(file_loc, 'r')
            zip_ref.extractall(output_path + st + description)
            zip_ref.close()
            
             # rename files
            for file in os.listdir(output_path+st):
                full_file = output_path + st + '/' + file
                if (os.path.getmtime(full_file) > start_time):
                    os.rename(full_file, output_path + st + description + file[-4:])
            
            # remove zip file
            os.remove(file_loc)
        except:
            print ('FAILED ' + st + ' ' + description)


#%%
from census import Census
c = Census('b5f46e9fc4d18d5f373ba883268917fb318356a6')

#%%
census_vars = ['GEO_ID']
info_dict = c.acs5.state_county_blockgroup(census_vars,
                                          FIPS['VA'],
                                          '500', # county. you might have to loop over this?
                                          c.ALL, # which block groups do you want
                                          year=2010)

df = pd.DataFrame(info_dict)
#%%
path = 'C:/Users/Jacob/Desktop/JP/2010/'
for state in FIPS:
    for file in os.listdir(path+state):
        os.rename(path+state+'/'+file, path+state+'/census_blocks_as_downloaded' + file[-4:])
#%%
def extract_cb_data_from_census_API(census_wrapper, fields, state, yr):
    county_query = c.sf1.state_county(['NAME'], FIPS[state], c.ALL, year=yr)
    counties = [entry['county'] for entry in county_query]
    
    df = pd.DataFrame()
    for county in counties:
        info_dict = c.sf1.state_county_blockgroup(fields,
                                              FIPS[state],
                                              county,
                                              c.ALL, # which block groups do you want
                                              year=yr)
        info_df = pd.DataFrame(info_dict)
        df = pd.concat([df, info_df])
    return df
#%%
def separate_national_shp_into_states(states, geo_df, state_id, output_path, description):
    ''' Separates national shapefile into files by state
    
    Arguments: 
        states: dictionary of states and corresponding URLs
        geo_df: geopandas dataframe from national shapefile
        state_id: column name for states in geo_df
        output_path: path to directory for state output folder
        description: what we are creating, with a / at the start
            (example: /112_congress)
    '''  
    for st in states:
        out_df = geo_df.loc[geo_df[str(state_id)] == states[st]]
        
        if not os.path.isdir(output_path + st + description):
            os.mkdir(output_path + st + description)
        out_df.to_file(output_path + st + description + '/shapes.shp')
#%%
def add_populations_to_block_groups(files, dfs_with_pop, merge_id, output_path, description):
    
    for st in files:
        
        # extract geo_dataframe from link
        df1 = gpd.read_file(files[st])
        print (df1.columns)
        
        # get corresponding df with population
        df2 = dfs_with_pop[st]
        
        # merge
        merged = df1.merge(df2, how='left', on=merge_id,)

        # write to file
        if not os.path.isdir(output_path + st + description):
            os.mkdir(output_path + st + description)
        merged.to_file(output_path + st + description + '/shapes.shp')
#%%
def assign_block_groups_to_districts(bg_df, dist_df, output_file):
    
    # initialize list of dicts
    district_proportions = []
    
    # iterate over block groups
    for _, bg in bg_df.iterrows():
        districts = {}
        bg_geometry = bg['geometry']
        bg_area = bg_geometry.area
        for ix, dist in dist_df.iterrows():
            dist_geometry = dist['geometry']
            intersection_area = (bg_geometry.intersection(dist_geometry)).area
            districts[ix] = intersection_area/bg_area
            if sum(districts.values()) > 0.999:
                break
        district_proportions.append(districts)
    
    # output pickle file
    output_df = pd.DataFrame(bg_df.drop(columns='geometry'))
    output_df['DISTRICTS'] = district_proportions
    output_df.to_pickle(output_file)
    return output_df
            
#%%
for congress in [112, 113, 114, 115, 116]:
    for st in FIPS:
        bg_file = 'C:/Users/Jacob/Desktop/JP/2010/' + st + '/block_groups_with_pop/shapes.shp'
        dist_file = 'C:/Users/Jacob/Desktop/JP/2010/' + st + '/' + str(congress) + '_congress/shapes.shp'
        bg_df = gpd.read_file(bg_file)
        dist_df = gpd.read_file(dist_file)
        output_file = 'C:/Users/Jacob/Desktop/JP/2010/' + st + '/' + str(congress) + '_congress/block_groups.pkl'
        assign_block_groups_to_districts(bg_df, dist_df, output_file)
        
#%%
for congress in [108, 109, 110, 111]:
    for st in FIPS:
        bg_file = 'C:/Users/Jacob/Desktop/JP/2010/' + st + '/block_groups_with_pop/shapes.shp'
        
        # get dist_file
        for file in os.listdir('C:/Users/Jacob/Desktop/JP/2000/' + st + '/' + str(congress) + '_congress'):
            if file[-4:] == '.shp':
                dist_file = 'C:/Users/Jacob/Desktop/JP/2000/' + st + '/' + str(congress) + '_congress/' + file
        bg_df = gpd.read_file(bg_file)
        dist_df = gpd.read_file(dist_file)
        output_file = 'C:/Users/Jacob/Desktop/JP/2010/' + st + '/' + str(congress) + '_congress/block_groups.pkl'
        if not os.path.isdir('C:/Users/Jacob/Desktop/JP/2010/' + st + '/' + str(congress)+ '_congress'):
            os.mkdir('C:/Users/Jacob/Desktop/JP/2010/' + st + '/' + str(congress)+ '_congress')
        assign_block_groups_to_districts(bg_df, dist_df, output_file)
        
#%%
for st in FIPS:
    df = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/' + st + '/block_groups_with_pop/shapes.shp')
    good = len(df.loc[df['P001001'] != None])
    total = len(df)
    print(st + ' ' + str(good/total))
#%%
merge_id = ['GEO_ID']
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/block_groups_with_pop'

files_2010 = {}
pops_2010 = {}

for st in FIPS:
    files_2010[st] = 'C:/Users/Jacob/Desktop/JP/2010/'+ st + '/block_groups/gz_2010_' + FIPS[st] + '_150_00_500k.shp'
for st in FIPS:
    print(st)
    pops_2010[st] = extract_cb_data_from_census_API(c, ['GEO_ID', 'P001001'], st, 2010)
add_populations_to_block_groups(files_2010, pops_2010, merge_id, output_path, description)
#%%
congress_111 = {}
for st in FIPS:
    congress_111[st] = 'http://www2.census.gov/geo/tiger/GENZ2010/gz_2010_' + FIPS[st] +'_500_11_500k.zip'
download_files(congress_111, 'C:/Users/Jacob/Desktop/JP/2010/', '/111_congress')
#%%
congress_110 = {}
for st in FIPS:
    congress_110[st] = 'http://www2.census.gov/geo/tiger/PREVGENZ/cd/cd110shp/cd' + FIPS[st] +'_110_shp.zip'
download_files(congress_110, 'C:/Users/Jacob/Desktop/JP/2010/', '/110_congress')
#%%
congress_109 = {}
for st in FIPS:
    congress_109[st] = 'http://www2.census.gov/geo/tiger/PREVGENZ/cd/cd109shp/cd' + FIPS[st] +'_109_shp.zip'
download_files(congress_109, 'C:/Users/Jacob/Desktop/JP/2010/', '/109_congress')
#%%
congress_108 = {}
for st in FIPS:
    congress_108[st] = 'http://www2.census.gov/geo/tiger/PREVGENZ/cd/cd108shp/cd' + FIPS[st] +'_108_shp.zip'
download_files(congress_108, 'C:/Users/Jacob/Desktop/JP/2010/', '/108_congress')
#%%
upper_leg_2017 = {}
for st in FIPS:
    upper_leg_2017[st] = 'http://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_' + FIPS[st] + '_sldu_500k.zip'
download_files(upper_leg_2017, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2017')
#%%
lower_leg_2017 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2017[st] = 'http://www2.census.gov/geo/tiger/GENZ2017/shp/cb_2017_'+FIPS[st]+'_sldl_500k.zip'
download_files(lower_leg_2017, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2017')
#%%
upper_leg_2016 = {}
for st in FIPS:
    upper_leg_2016[st] = 'http://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_' + FIPS[st] + '_sldu_500k.zip'
download_files(upper_leg_2016, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2016')
#%%
lower_leg_2016 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2016[st] = 'http://www2.census.gov/geo/tiger/GENZ2016/shp/cb_2016_'+FIPS[st]+'_sldl_500k.zip'
download_files(lower_leg_2016, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2016')
#%%
upper_leg_2015 = {}
for st in FIPS:
    upper_leg_2015[st] = 'http://www2.census.gov/geo/tiger/GENZ2015/shp/cb_2015_' + FIPS[st] + '_sldu_500k.zip'
download_files(upper_leg_2015, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2015')
#%%
lower_leg_2015 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2015[st] = 'http://www2.census.gov/geo/tiger/GENZ2015/shp/cb_2015_'+FIPS[st]+'_sldl_500k.zip'
download_files(lower_leg_2015, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2015')
#%%
upper_leg_2014 = {}
for st in FIPS:
    upper_leg_2014[st] = 'http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_' + FIPS[st] + '_sldu_500k.zip'
download_files(upper_leg_2014, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2014')
#%%
lower_leg_2014 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2014[st] = 'http://www2.census.gov/geo/tiger/GENZ2014/shp/cb_2014_'+FIPS[st]+'_sldl_500k.zip'
download_files(lower_leg_2014, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2014')
#%%
upper_leg_2013 = {}
for st in FIPS:
    upper_leg_2013[st] = 'http://www2.census.gov/geo/tiger/GENZ2013/cb_2013_' + FIPS[st] + '_sldu_500k.zip'
download_files(upper_leg_2013, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2013')
#%%
lower_leg_2013 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2013[st] = 'http://www2.census.gov/geo/tiger/GENZ2013/cb_2013_'+FIPS[st]+'_sldl_500k.zip'
download_files(lower_leg_2013, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2013')
#%%
upper_leg_2010 = {}
for st in FIPS:
    upper_leg_2010[st] = 'http://www2.census.gov/geo/tiger/GENZ2010/gz_2010_' + FIPS[st] + '_610_u2_500k.zip'
download_files(upper_leg_2010, 'C:/Users/Jacob/Desktop/JP/2010/', '/upper_leg_2010')
#%%
lower_leg_2010 = {}
for st in FIPS:
    if st is not 'NE' and st is not 'DC':
        lower_leg_2010[st] = 'http://www2.census.gov/geo/tiger/GENZ2010/gz_2010_'+FIPS[st]+'_620_l2_500k.zip'
download_files(lower_leg_2010, 'C:/Users/Jacob/Desktop/JP/2010/', '/lower_leg_2010')
#%%
upper_leg_2006 = {}
for st in FIPS:
    upper_leg_2006[st] = 'http://www2.census.gov/geo/tiger/PREVGENZ/su/su06shp/su' + FIPS[st] + '_d11_shp.zip'
download_files(upper_leg_2006, 'C:/Users/Jacob/Desktop/JP/2000/', '/upper_leg_2006')
#%%
lower_leg_2006 = {}
for st in FIPS:
    lower_leg_2006[st] = 'http://www2.census.gov/geo/tiger/PREVGENZ/sl/sl06shp/sl' + FIPS[st] + '_d11_shp.zip'
download_files(lower_leg_2006, 'C:/Users/Jacob/Desktop/JP/2000/', '/lower_leg_2006')
#%%
block_groups_2010 = {}
for st in FIPS:
    block_groups_2010[st] = 'https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_' + FIPS[st] + '_150_00_500k.zip'
download_files(block_groups_2010, 'C:/Users/Jacob/Desktop/JP/2010/', '/block_groups')
#%%
block_groups_2000 = {}
for st in FIPS:
    block_groups_2000[st] = 'https://www2.census.gov/geo/tiger/PREVGENZ/bg/bg00shp/bg' + FIPS[st] + '_d00_shp.zip'
download_files(block_groups_2000, 'C:/Users/Jacob/Desktop/JP/2000/', '/block_groups')
#%%
for st in FIPS:
    for file in os.listdir('C:/Users/Jacob/Desktop/JP/2000/'+st+'/block_groups'):
        os.remove('C:/Users/Jacob/Desktop/JP/2000/'+st+'/block_groups/'+file)
    os.rmdir('C:/Users/Jacob/Desktop/JP/2000/'+st+'/block_groups')
#%%
shapefile = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/11_congress/tl_2018_us_cd116.shp')
state_id = 'STATEFP'
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/116_congress'
separate_national_shp_into_states(FIPS, shapefile, state_id, output_path, description)
#%%
shapefile = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/115_congress/tl_2017_us_cd115.shp')
state_id = 'STATEFP'
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/115_congress'
separate_national_shp_into_states(FIPS, shapefile, state_id, output_path, description)
#%%
shapefile = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/114_congress/tl_2015_us_cd114.shp')
state_id = 'STATEFP'
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/114_congress'
separate_national_shp_into_states(FIPS, shapefile, state_id, output_path, description)
#%%
shapefile = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/113_congress/tl_2013_us_cd113.shp')
state_id = 'STATEFP'
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/113_congress'
separate_national_shp_into_states(FIPS, shapefile, state_id, output_path, description)
#%%
shapefile = gpd.read_file('C:/Users/Jacob/Desktop/JP/2010/112_congress/tl_2011_us_cd112.shp')
state_id = 'STATEFP'
output_path = 'C:/Users/Jacob/Desktop/JP/2010/'
description = '/112_congress'
separate_national_shp_into_states(FIPS, shapefile, state_id, output_path, description)
#%%

def read_congressional_district_shapefiles(maps, output_path, state_id):
    ''' Reads congressional district shapefiles and separates them by
    state.
    
    Arguments: 
        maps: dictionary whose keys are the names of the districting plan
            (e.g. 112_congress) and whose values are the full file paths
            where the corresponding shapefile lies
        output_path: folder where state-by-state shapefiles should go
        state_id: column in attribute table that contains FIPS code
            (operates under assumption that this is the same for all maps)
    '''
    for plan in maps:
        
        # read in file to geodataframe
        geo_df = gpd.read_file(maps[plan])
        
        # trim geo_df to actual districts (removing territories, unassigned
        # "districts," and other weird data artifacts)
        geo_df = geo_df.loc[geo_df['FUNCSTAT'] == 'N']
        geo_df =  geo_df.loc[int(geo_df['GEOID']) % 100 <= 53]
        
        # check that this worked
        if (len(geo_df) != 435):
            raise Exception('CD shapefile at ' + path + ' has ' + \
                            str(len(geo_df)) + ' elements after cleaning')
        
        # get FIPS of all states included in shapefile
        df_FIPS = list(set(geo_df.loc[:, state_id]))
        df_FIPS = [int(i) for i in df_FIPS]
        
        # separate shapefiles by state
        for state in FIPS:
            fips = int(FIPS[state])
            # check if this state is in the shapefile (maybe needed for DC, PR)
            if fips in df_FIPS:
                
                # trim df for appropriate rows
                state_df = geo_df.loc[int(geo_df[state_id]) == fips]
                
                # save file to appropriate location
                directory = output_path + state
                if not os.path.isdir(directory):
                    os.mkdir(directory)
                state_df.to_file(directory + '/' + plan + '.shp')
                
#%%
def download_census_block_files(output_path):
    
    for state in ['AK']:
        # read in file
        file = 'https://www2.census.gov/geo/tiger/TIGER2010BLKPOPHU/' + \
               'tabblock2010_' + FIPS[state] + '_pophu.zip'	
        
        # download
        if not os.path.isdir(output_path + 'temp'):
            os.mkdir(output_path + 'temp')
        file_loc = output_path + 'temp/temp.zip'
        
        urllib.request.urlretrieve(file, file_loc)
    
        # unzip
        zip_ref = zipfile.ZipFile(file_loc, 'r')
        zip_ref.extractall(output_path + 'temp')
        zip_ref.close()
        
        for file in os.listdir(output_path + '/temp'):
            full_file = output_path + 'temp/' + file
            if file[-4:] == '.shp':
                geo_df = gpd.read_file(full_file)
        
        # remove temp folder
        shutil.rmtree(output_path + 'temp')
        
        # delete census blocks with no population
        geo_df = geo_df.loc[geo_df['POP10'] > 0]
        
        # write census block shapefile
        geo_df.to_file(output_path + state + '/' + '2010_blocks.shp')

def separate_national_shp_into_states(geo_df, state_id, output_path, name):
    ''' Separates national shapefile into files by state
    
    Arguments: 
        geo_df: geopandas dataframe from national shapefile
        state_id: column name for states in geo_df
        output_path: path to directory for state output folder
        name: name the output shapefile (example: 2010_counties)
    '''  
    for st in FIPS:
        out_df = geo_df.loc[geo_df[str(state_id)] == FIPS[st]]
        
        if not os.path.isdir(output_path + st):
            os.mkdir(output_path + st)
        out_df.to_file(output_path + st + '/' + name + '.shp')
    