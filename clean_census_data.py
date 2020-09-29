"""Clean all relevant census data."""
import os
import geopandas as gpd
from pull_census_data import state_fips


def main():
    """Clean all census data in preparation for analysis

    We start by creating new folders

    Next, we split nationwide shapefiles into statewide shapefiles

    Then, we rename and move state legislative districts

    Afterwards, we join census geography data to census population data

    Finally, we remove duplicative boundary shapefiles
    """
    # Get list of state fips
    fips = state_fips()

    # Create folders for each state
    create_state_directories(fips)

    # Split nationwide files into state files
    split_counties(fips)
    split_congressional_districts(fips)

    # Move state legislative districts
    # move_state_legislative_districts()

    # Join census data
    # join_census_geo_and_pop()

    # Remove duplicative boundaries
    # remove_duplicative_boundaries()

    return


def split_counties(fips):
    """Split counties by state.

    Arguments:
        fips: dictionary with key as state abbreviation and fips code as
            element
    """
    # Display steps
    print('SPLITTING NATIONWIDE COUNTY GEOGRAPHIES' + '\n\n')

    # Iterate through extracted counties folder
    folders = os.listdir('extract_census/county')
    for folder in folders:
        # Get the files in the folder then the shapefile name
        direc = 'extract_census/county/' + folder
        file = os.listdir(direc)[0][:-4] + '.shp'

        # Load the nationwide shapefile
        df_us = gpd.read_file(direc + '/' + file)

        # Get the name of the state fips columns
        fips_col = 'STATEFP'
        year = file[3:7]
        if file[-6:-4] == '00':
            fips_col += '00'
            year = '2000'
        elif file[-6:-4] == '10':
            fips_col += '10'
            year = '2010'

        # For each state split the dataframe
        for state, fips_code in fips.items():
            # Check if already exists
            output = 'clean_data/' + state + '/'
            output += state + '_county_' + year + '.shp'
            if not os.path.exists(output):
                # Slice and save
                print(output)
                df_state = df_us[df_us[fips_col] == fips_code]
                df_state.to_file(output)

    return


def split_congressional_districts(fips):
    """Split congressional districts by state.

    Arguments:
        fips: dictionary with key as state abbreviation and fips code as
            element
    """
    # Display steps
    print('SPLITTING NATIONWIDE CONGRESSIONAL DISTRICT GEOGRAPHIES' + '\n\n')

    # Iterate through extracted counties folder
    folders = os.listdir('extract_census/cd')
    for folder in folders:
        # Get the files in the folder then the shapefile name
        direc = 'extract_census/cd/' + folder
        file = os.listdir(direc)[0][:-4] + '.shp'

        # Load the nationwide shapefile
        df_us = gpd.read_file(direc + '/' + file)

        # Get the name of the state fips columns
        fips_col = 'STATEFP'
        year = file[3:7]
        if file[-7:-4] == '108':
            fips_col += '00'
            year = '2003'
        elif file[-7:-4] == '111':
            fips_col += '10'
            year = '2010'

        # For each state split the dataframe
        for state, fips_code in fips.items():
            # Check if already exists
            output = 'clean_data/' + state + '/'
            output += state + '_cd_' + year + '.shp'
            if not os.path.exists(output):
                # Slice and save
                print(output)
                df_state = df_us[df_us[fips_col] == fips_code]
                df_state.to_file(output)

    return


def create_state_directories(fips):
    """Create state based directories.

    Arguments:
        fips: dictionary with key as state abbreviation and fips code as
            element
    """
    # Create base directory
    if not os.path.exists('clean_data'):
        os.makedirs('clean_data')

    # Create state directories
    for state, fips_code in fips.items():
        if not os.path.exists('clean_data/' + state):
            os.makedirs('clean_data/' + state)


if __name__ == "__main__":
    main()
