import json
import re
import numpy as np
import os
import fnmatch
import glob
import copy


def addAttribute(db, attr):
    """
    addAttribute(db, attr)

    Function loops over datasets in an xsearch path dictionary and
    adds or updates the dictionary to include a dataset attribute.

    Inputs
        db dict: Dictionary of results to search
        attr str: Attribute to add to dictionary

    Returns
        pathDict Dict: New dictionry with attr included

    Note: If attribute does not exist, it will not be added. Function will
    import and use xarray to open datasets.
    """
    # make sure xarray is imported
    import xarray as xr
    # make a copy of the original dictionary
    db_new = copy.deepcopy(db)
    # loop over each dataset and fetch the attribute of interest
    for p in db.keys():
        # load dataset
        ds = xr.open_mfdataset(p + '/*.nc')
        attrs = ds.attrs
        if attr not in attrs:
            continue
        else:
            attr_value = attrs[attr]
            db_new[p][attr] = attr_value
    return db_new


def getGroupValues(db, facet):
    """
    getGroupValues(db, facet)

    Inputs
        db dict: Dictionary of results to search
        facet str: facet name to search

    Returns
        values list: All unique facet values
    """
    values = []
    for key in db.keys():
        value = db[key][facet]
        if value not in values:
            values.append(value)
    return values


def retainDataByFacetValue(db, facet, value):
    """
    retainDataByFacetValue(db, facet, value)

    Inputs
        db dict: Dictionary of results to search
        facet str: facet name to search
        value str: value to retain

    Returns
        values dict: dictionary with all items dropped, except
                     those matching the facet-value pairing
    """
    db_copy = db.copy()
    keyList = list(db_copy.keys())
    for key in keyList:
        if db_copy[key][facet] != value:
            db_copy.pop(key)
    return db_copy


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def versionWeight(V):
    """
    V = versionWeight(ver).

    versionWeight takes a version string for a CMIP xml and returns a
    numeric in which the larger the number, the more recent the version.
    Typically an int corresponding to the date (e.g., 20190829), but will
    give precedence to version numbers (e.g., v1 is returned as 100000000).
    """
    V = V.replace('-tmp', '')
    if V == 'latest':
        V = 0
    else:
        V = int(V.replace('v', ''))
        if V < 10:
            V = V*100000000
    V = int(V)
    return V


def filter_dpaths(dpaths, modelData, crit):
    """
    OutList = filter_dpaths(files, keyMap, crit).

    Function to narrow down the number of paths in a list based on
    file metadata and selection criteria.

    Inputs:
        dpaths:        list of file paths
        modelData:     dictionary (xml filenames are keys) which includes
                       the metadata associated with the xml (e.g., ver, cdate,
                       publish, tpoints)
        crit:          string of criteria (e.g., 'tpoints') in which to filter
                       the input list of files

    filter_dpaths will take the top value(s) from the list. For example, if
    the filter criteria is 'publish' and a list with two republished and two
    unpublished files are passed to the function, the two published files
    will be returned. The criteria can be boolean or int (will return True
    booleans and the max integer). Alternatively, if the criteria is creation
    date it will return files with the most recent creation date

    If only one file is in the list, the original list is returned (with
    one file).
    """
    if len(dpaths) < 2:
        return dpaths
    # get values
    values = []
    for dpath in dpaths:
        if crit == 'esgf_publish':
            if 'esgf_publish' in dpath:
                v = 1
            else:
                v = 0
        elif crit == 'gr':
            if 'gr' in dpath:
                v = 1
            else:
                v = 0
        elif crit == 'nc_creation_date':
            v = int(modelData[dpath][crit])
        else:
            v = modelData[dpath][crit]
        if crit == 'version':
            v = versionWeight(v)
        values.append(v)
    # determine optimal value
    if type(v) == int:
        vmax = np.max(values)
    else:
        vmax = True
    # create output list
    OutList = []
    for v, dpath in zip(values, dpaths):
        if v == vmax:
            OutList.append(dpath)
            
    return OutList


def findPaths(experiment,
              variable,
              frequency,
              jsonDir='/p/user_pub/xclim/persist/xsearch/',
              criteria=['version', 'timepoints', 'nc_creation_date', 'esgf_publish', 'gr'],
              verbose=True,
              deduplicate=True,
              printDuplicates=False,
              lcpath=False,
              nimbuspath=False,
              filterRetired=True,
              filterRetracted=True,
              filterIgnored=True,
              fullMetadata=True,
              **kwargs):
    """
    findPaths

    Inputs:
        experiment str: experiment id to search for
        variable str: variable id to search for
        frequency str: frequency id to search for

    Optional Inputs:
        jsonDir str:            directory of json lookup files (default /p/user_pub/xclim/persist/json/)
        criteria list:          order of criteria to filter paths (default ['version', 'timepoints', 'creation_date'])
                                where version is the string version_id, timepoints is the number of time steps, and
                                creation_date is the creation date in the dataset header
        lcpath Bool:            flag to denote whether search is on an LC system (data path is different on LC systems)
        nimbuspath Bool:        flag to denote search is on an Nimbus system (data path is different on Nimbus)
        deduplicate Bool:       flag to de-duplicate datasets for the same model/realization
        filterRetracted Bool:   flag to ignore retracted datasets (if True; default True)
        filterIgnored Bool:     flag to ignore datasets marked as ignored (if True; default True)
        fullMetadata Bool:      flag to return full set of metadata (True) or a list of paths (False); default False

    Keyword arguments:
        The user can also additionally filter results by keyword argument (mip_era, activity, institute,
        model, member, cmipTable, realm, grid, or gridLabel)

    Returns:
        pathDict (list | dict): Either returns a list of paths matching search criteria (fullMetadata = False) or a 
                                dictionary with keys as the datasets. In the dictionary, each entry contains a dictionary
                                entry with metadata for that dataset. If applicable, alternate_paths are also listed
                                and whether the dataset was uniquely chosen based on the filter criteria.
    """
    # define json file search
    fn = jsonDir + experiment + '/' + variable + '.json'
    if lcpath:
        fn = fn.replace('/p/', '/p/climate/')
    if nimbuspath:
        fn = fn.replace('/p/', '/home/jovyan/local-data/')
    # load data
    files = glob.glob(fn)
    # loop over all json files and store
    # in common dictionary
    data = {}
    for fn in files:
        f = open(fn, 'r')
        data_subset = json.load(f)
        f.close()
        data = {**data, **data_subset}
    if len(files) == 0:
        if fullMetadata:
            return {}
        else:
            return []
    # whittle down by frequency and variable
    rmpaths = []
    for dpath in data.keys():
        if data[dpath]['frequency'] != frequency:
            rmpaths.append(dpath)
    # filter paths
    for dpath in rmpaths:
        data.pop(dpath)
    if lcpath:
        dataold = data.copy()
        data = {}
        for dpath in dataold.keys():
            dpathlc = dpath.replace('/p/', '/p/climate/')
            data[dpathlc] = dataold[dpath]
        del dataold
    pathDict = {}
    # get user specified filters
    filterDict = {}
    for key in kwargs.keys():
        v = kwargs[key]
        if type(v) == str:
            v = v
        filterDict[key] = v
    if filterRetired:
        filterDict['retired'] = 0
    if filterRetracted:
        filterDict['retracted'] = 0
    if filterIgnored:
        filterDict['ignored'] = 0
    # determine paths to filter
    rmpaths = []
    for dpath in data.keys():
        for key in filterDict.keys():
            v = data[dpath][key]
            rmp = False
            if type(v) == int:
                if v != filterDict[key]:
                    rmp = True
            else:
                if not fnmatch.fnmatch(v, filterDict[key]):
                    rmp = True
            if (rmp & (dpath not in rmpaths)):
                rmpaths.append(dpath)
    # filter paths
    for dpath in rmpaths:
        data.pop(dpath)
    # if filter not specified, get all possible values
    for key in ['activity', 'cmipTable', 'realm', 'variable', 'experiment', 'frequency']:
        if key not in filterDict.keys():
            filterDict[key] = getGroupValues(data, key)
    # get model list
    models = getGroupValues(data, 'model')
    # warn user that some datasets have multiple attributes
    if verbose:
        for key in ['activity', 'cmipTable', 'realm', 'variable', 'experiment', 'frequency']:
            if ((len(filterDict[key]) > 1) & (key not in kwargs.keys())):
                print('Multiple values for ' + key + '. Consider filtering by ' + key + '.')
                print('Available values: ' + ', '.join(filterDict[key]))
                print()
    # loop over each model to get model-specific data
    if deduplicate:
        for model in models:
            # create model specific dictionary
            modelData = data.copy()
            modelData = retainDataByFacetValue(modelData, 'model', model)
            # get all paths for each model member
            memberGroups = {}
            for dpath in modelData.keys():
                ripf = modelData[dpath]['member']
                if ripf not in memberGroups.keys():
                    memberGroups[ripf] = [dpath]
                else:
                    memberGroups[ripf] = memberGroups[ripf] + [dpath]
            # prioritize / de-duplicate model members
            for member in memberGroups.keys():
                dplist = memberGroups[member].copy()
                if len(dplist) == 0:
                    continue
                if len(dplist) > 1:
                    for crit in criteria:
                        try:
                            dplist = filter_dpaths(dplist, modelData, crit)
                        except:
                            continue
                # continue whittling down path list until only one is left
                # by iteratively using each criteria
                olist = memberGroups[member]
                olist.remove(dplist[0])
                dpath = dplist[0]
                dd = data[dpath]
                if len(dplist) == 1:
                    dd['unique'] = True
                else:
                    dd['unique'] = False
                dd['alternate_paths'] = olist
                pathDict[dpath] = dd
    else:
        for dpath in data.keys():
            dd = data[dpath]
            pathDict[dpath] = dd
    if (printDuplicates & deduplicate):
        print('Chosen values')
        for dpath in pathDict.keys():
            ap = pathDict[dpath]['alternate_paths']
            print('* ' + dpath)
            if len(ap) > 1:
                for p in ap:
                    print('     duplicate: ' + p)
    if fullMetadata:
        return pathDict
    else:
        pathlist = []
        for dpath in pathDict.keys():
            pathlist.append(dpath)
        pathlist.sort()
        return pathlist


def getValuesForFacet(db, facet, value):
    """
    getValuesForFacet(db, facet, value)

    Inputs
        db dict: Dictionary of results to search
        facet str: facet name to search
        value str: value of facet

    Returns
        pathList list: Entries in dictionary matching facet-value pairing
    """
    result = []
    for key in db.keys():
        if fnmatch.fnmatch(db[key][facet], value):
            result.append(key)
    result = natural_sort(result)
    return result

