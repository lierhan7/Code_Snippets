from pyopenms import *


def feature_detection(exp, mtd_custom_params={}, epd_custom_params={}, ffm_custom_params={}, mzML_file_name=''):
    """Feature detection with the FeatureFinderMetabo.

    Parameters
    ----------
    exp : pyopenms.MSExperiment
        MSExperiment to detect features from.
    mtd_params : dict
        Custom parameters for MassTraceDetection.
    epd_params : dict
        Custom parameters for ElutionPeakDetection.
    ffm_params : dict
        Custom parameters for FeatureFinderMetabo.
    mzML_file_name : str
        Path to experiment mzML file to set as PrimaryMSRunPath in FeatureMap.

    Returns
    -------
    pyopenms.FeatureMap
        FeatureMap with detected features.
    """
    exp.sortSpectra(True)
    mass_traces = []
    mtd = MassTraceDetection()
    mtd_params = mtd.getDefaults()
    for k, v in mtd_custom_params.items():
        mtd_params.setValue(k, v)
    mtd.setParameters(mtd_params)
    mtd.run(exp, mass_traces, 0)

    mass_traces_split = []
    mass_traces_final = []
    epd = ElutionPeakDetection()
    epd_params = epd.getDefaults()
    for k, v in epd_custom_params.items():
        epd_params.setValue(k, v)
    epd.setParameters(epd_params)
    epd.detectPeaks(mass_traces, mass_traces_split)

    if (epd.getParameters().getValue("width_filtering") == "auto"):
        epd.filterByPeakWidth(mass_traces_split, mass_traces_final)
    else:
        mass_traces_final = mass_traces_split

    feature_map_FFM = FeatureMap()
    feat_chrom = []
    ffm = FeatureFindingMetabo()
    ffm_params = ffm.getDefaults()
    for k, v in ffm_custom_params.items():
        ffm_params.setValue(k, v)
    ffm.setParameters(ffm_params)
    ffm.run(mass_traces_final, feature_map_FFM, feat_chrom)
    feature_map_FFM.setUniqueIds()
    feature_map_FFM.setPrimaryMSRunPath([mzML_file_name.encode()])

    return feature_map_FFM


mzML_file_path = 'path/to/mzML'

exp = MSExperiment()
MzMLFile().load(mzML_file_path, exp)

fm = feature_detection(exp,
                       mzML_file_name=mzML_file_path,
                       mtd_custom_params={"mass_error_ppm": 5.0,
                                          "noise_threshold_int": 1000.0
                                          },
                       epd_custom_params={"width_filtering": "fixed"
                                          },
                       ffm_custom_params={"isotope_filtering_model": "none",
                                          "remove_single_traces": "false",
                                          "mz_scoring_by_elements": "false",
                                          "report_convex_hulls": "true"
                                          })
