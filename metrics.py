"""Calculate County Splits Metrics."""
import numpy as np


def threshold(pops, threshold=50):
    ''' Remove elements of a dictionary with values below a certain threshold.

    Used for small district county intersections that are effectively
    errors in the geographic files

    Arguments:
        pops: dictionary whose keys are ordered pairs (county, district)
            and whose values are the populations within these intersections.
        threshold: vlaue below which we filter out

    Output:
        thresholded pops dictionary
    '''
    keys_to_remove = [key for key in pops if pops[key] < threshold]
    for key in keys_to_remove:
        pops.pop(key, None)
    return pops


def counties_split(pops):
    """Get the number of counties with splits"""
    # Get set of all counties
    counties = set([key[0] for key in pops])

    # List of ones if county is split by the districts
    split_counties = [1 for county in counties
                      if len([key for key in pops if key[0] == county]) > 1]

    return sum(split_counties)


def county_intersections(pops):
    """Get the total number of county district splits."""
    return len(pops)


def preserved_pairs(pops):
    ''' Calculates preserved_pairs given population intersections
    between districts and counties

    Arguments:
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.

    Output:
        preserved_pairs (number between 0 and 1): the probability that
        two randomly chosen people from the same county are also
        in the same district.

        Some research shows this is from Rand (1971) and Wallace (1983)
    '''
    # get number of pairs in same county and same district
    same_county_same_district = sum([i * (i - 1) / 2 for i in pops.values()])

    # get counties
    counties = set([key[0] for key in pops])

    # get number of pairs in same county
    county_pops = [sum([pops[key] for key in pops if key[0] == county])
                   for county in counties]
    same_county = sum([i * (i - 1) / 2 for i in county_pops])

    # calculate and return PICS
    PICS = same_county_same_district / same_county
    return PICS


def largest_intersection(pops):
    ''' Calculates largest_intersection given population intersections between
    districts and counties

    Arguments:
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.


    Output:
        largest_intersection (number between 0 and 1): the fraction of voters
        who are in the congressional district that has the largest number of
        their county's voters.  Alternatively, if everyone assumed that
        their congressional district was the one with the largest number
        of their county's residents, the proportion who would be correct.

    # Adaptation of criterion here
        https://doi.org/10.1080/01621459.1954.10501231
    '''
    # get counties
    counties = set([key[0] for key in pops])

    # get size of largest intersection in each county
    county_maxes = [max([pops[key] for key in pops if key[0] == county])
                    for county in counties]

    # calculate and return GK
    GK = sum(county_maxes) / sum(pops.values())
    return GK


def min_entropy(pops):
    ''' Calculates conditional entropy of district partition with respect to
        county partition

    Arguments:
        pops: dictionary whose keys are ordered pairs (county, district)
        and whose values are the populations within these intersections.

    Output:
        min_entropy, scaled to be in (0,1) such that more similar parititions
        yield a higher number'''

    # get counties
    counties = set([key[0] for key in pops])

    # compile lists to sum
    county_entropies = []
    for county in counties:
        districts = [key for key in pops if key[0] == county]
        county_size = sum([pops[key] for key in districts])
        county_entropy = sum([pops[key] * np.log2(pops[key] / county_size)
                              for key in districts])
        county_entropies.append(county_entropy)

    # calcuate conditional entropy, return reciprocal
    c_entropy = (-1) * sum(county_entropies) / sum(pops.values())
    return 1 / (1 + c_entropy)
