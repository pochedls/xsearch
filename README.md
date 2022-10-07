# xsearch search utility

### Overview

This repository tracks the `xsearch` utility, which allows PCMDI users to query CMIP5 and CMIP6 data. The utility returns dataset paths for a given search criteria.

These dataset directories can be used with [xarray](https://docs.xarray.dev/en/stable/) and [xcdat](https://xcdat.readthedocs.io/en/latest/) to open and read the data (e.g., via `xcdat.open_mfdataset()`). The `x` in `xsearch` denotes that the search is supposed to complement `xarray` and `xcdat`.

`xsearch` makes use of json files that store dataset directories and associated metadata. The json files are organized by experiment and variable: `jsonDirectory/experiment/variable.json`.

### Getting Started

You should be able to add the xsearch package to your `PYTHONPATH`. In your `.bashrc` file,

    export PYTHONPATH='/PATH/TO/XSEARCH/'

If the xsearch version is incremented you will receive a warning on import:

> Note that xsearch has been updated to version 0.0.2.
>
> You were last using version 0.0.1.

xsearch will create a file in your home directory to support version checking.

Alternatively, you can download the contents of this repository and import the package (or the `search.py` file).

`xsearch` is built around metadata logic documented in the [CMIP6 Global Attributes, DRS, Filenames, Directory Structure, and CV’s document](https://goo.gl/v1drZl). These logic underpin the filename and directory creation, written by [CMOR](https://cmor.llnl.gov/) and other CMIP-writing libraries. The [CMIP6 CMOR Tables](https://github.com/PCMDI/cmip6-cmor-tables/tree/master/Tables) (e.g. Amon - designate A=atmospheric realm, and mon=monthly frequency), similar logic underpinned the [CMIP5](https://github.com/PCMDI/cmip5-cmor-tables/tree/master/Tables) and [CMIP3](https://github.com/PCMDI/cmip3-cmor-tables/tree/master/Tables) phases.

### Support

Note: this software library is designed to help PCMDI users search for CMIP data. If the search works correctly, but points to a dataset that has problems (e.g., a corrupted or incomplete dataset) these issues should not be logged as an issue / bug in this repository.

Contributions from users of this utility are critical (issue reports and contributed code to improve the package).

### Usage Examples

    import xsearch as xs

    dpaths = xs.findPaths('historical', 'tas', 'mon')  # always need to specify an experiment / variable / frequency

> Multiple values for cmipTable. Consider filtering by cmipTable.
> Available values: Amon, ImonGre, ImonAnt
>
> Multiple values for realm. Consider filtering by realm.
> Available values: atmos, landIce

The search warns that the returned paths include data that spans multiple realms and multiple tables. You can add optional facets to select one realm/table:

    dpaths = xs.findPaths('historical', 'tas', 'mon', realm='atmos', cmipTable='Amon')
    print(dpaths)

> ['/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/historical/mon/atmos/Amon/r1i1p1/v20120709/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/historical/mon/atmos/Amon/r2i1p1/v20120709/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1-m/historical/mon/atmos/Amon/r3i1p1/v20120709/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1/historical/mon/atmos/Amon/r1i1p1/v1/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1/historical/mon/atmos/Amon/r2i1p1/v1/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/BCC/bcc-csm1-1/historical/mon/atmos/Amon/r3i1p1/v1/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/CNRM-CERFACS/CNRM-CM5/historical/mon/atmos/Amon/r10i1p1/v20110901/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/CNRM-CERFACS/CNRM-CM5/historical/mon/atmos/Amon/r1i1p1/v20110901/tas/',
>  '/p/css03/cmip5_css01/data/cmip5/output1/CNRM-CERFACS/CNRM-CM5/historical/mon/atmos/Amon/r2i1p1/v20110901/tas/',
> ...

Other search facets include: mip_era (`CMIP5` or `CMIP6`), activity (e.g., `CMIP` or `ScenarioMIP`), institute (e.g., `E3SM-Project`), model (e.g., `E3SM-1-1`), member (e.g., `r1i1p1f1`), grid (e.g., `gn` or `gr`), or gridLabel (e.g., `glb-z1-gr`).

These additional search facets support wildcards (experiment, frequency, and variable cannot currently accept wildcard operators).

The user can also specify a number of optional arguments:

* `deduplicate` (default `True`): flag whether to de-duplicate so that a single dataset path is returned for each unique combination of model and member.
    * criteria: The ordering of criteria used to deduplicate. The default is `["version", "timepoints", "nc_creation_date", "esgf_publish", "gr"]`, which orders by a) newest version, number of timesteps, the creation_date embedded in netCDF file metadata, and a prioritization for data that has been published on ESGF and has the glabel `gr`.
* `printDuplicates` (default False): If True, all potential paths will be printed and paths that are chosen will be denoted with an asterisk
* `verbose` (default True): flag to print out information during the search
* `lcpath` (default False): flag to adjust the data directories to reflect the LC (Livermore Computing/LLNL HPC) mountpoint
* `filterRetired` (default True): flag to filter out datasets that are retired (datasets are retired if they are moved)
* `filterRetracted` (default True): flag to filter out datasets that are retracted
* `filterIgnored` (default True): flag to filter out datasets that have been marked as ignored
* `jsonDir` (str): This defaults to the current location for the json metadata files, but the user can modify this

By default, `xsearch` will simply return a list of paths. `xsearch` can also return the full metadata for selected paths by setting `fullMetadata=True`:

    dpaths = xs.findPaths('historical', 'tas', 'mon', realm='atmos', cmipTable='Amon', fullMetadata=True)
    p1 = list(dpaths.keys())[0]  # get first path
    dpaths[p1]

This option will instead return a dictionary for each path with a complete set of metadata for that dataset directory:

> {'keyid': 'CMIP5.CMIP.CNRM-CERFACS.CNRM-CM5.historical.r10i1p1.Amon.atmos.mon.tas.gu.glb-z1-gu.v20110901',
>
>  'mip_era': 'CMIP5',
>
>  'activity': 'CMIP',
>
>  'institute': 'CNRM-CERFACS',
>
>  'model': 'CNRM-CM5',
>
>  'experiment': 'historical',
>
>  'member': 'r10i1p1',
>
> ...

Each entry in the returned dictionary is a nested dictionary in which the dataset path is the key with the following entries: keyid, mip_era, activity, institute, model, experiment, member, cmipTable, realm, frequency, variable, grid, gridLabel, version, timepoints, nfiles, nc_creation_date, sumfilesize_bytes, has_zero_size_files, created, modified, accessed, retired, retire_datetime, retracted, retracted_datetime, ignored, ignored_datetime, comment, unique, alternate_paths.

For example, to get the model of one dataset directory, `p`, we would use:

    print(dpaths[p]['model'])

> CNRM-CM5

Several functions in `xsearch` can further use the full metadata dictionary returned by `xsearch`. One function allows the user to get all values for a given search facet:

    xs.getValuesForFacet(dpaths, 'model', 'E3SM*')

> ['/p/css03/esgf_publish/CMIP6/CMIP/E3SM-Project/E3SM-1-0/historical/r1i1p1f1/Amon/tas/gr/v20190913/',
>  '/p/css03/esgf_publish/CMIP6/CMIP/E3SM-Project/E3SM-1-0/historical/r2i1p1f1/Amon/tas/gr/v20190729/',
>  '/p/css03/esgf_publish/CMIP6/CMIP/E3SM-Project/E3SM-1-0/historical/r3i1p1f1/Amon/tas/gr/v20190729/',
> ...

This function supports wildcard searches. Another search function allows the users to get all values for a given facet:

     xs.getGroupValues(dpaths, 'model')

> ['CNRM-CM5',
>  'bcc-csm1-1',
>  'bcc-csm1-1-m',
>  'GFDL-CM2p1',
>  'GFDL-ESM2G',
>  'GFDL-ESM2M',
> ...

### Acknowledgements

Much of the de-duplication logic and ideas from this are from the [durolib](https://github.com/durack1/durolib) library, created by Paul Durack [@durack1](https://github.com/durack1) to search for CMIP data. durolib handled [CDAT](https://cdat.llnl.gov/) xml files, which could be used to read in multi-file datasets. Logic to produce the xml files was refactored in [xagg](https://github.com/pochedls/xagg). xagg xmls are being phased out in favor the current approach: rapidly searchable json files, which allow the users to locate datasets and read them in with xarray based tools. Stephen Po-Chedley [@pochedls](https://github.com/pochedls/) produced the `xsearch` initial version.