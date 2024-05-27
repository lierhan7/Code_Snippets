def get_polarity(mzml_file):

    polarity_list = []
    
    exp = oms.MSExperiment()
    oms.MzMLFile().load(mzml_file, exp)

    cut = 0
    for spectrum in exp:
        if cut == 10000:
            break
    
        # Retrieve the polarity from the instrument settings
        instrument_settings = spectrum.getInstrumentSettings()
        polarity = instrument_settings.getPolarity()
    
        # Translate the polarity enum into a human-readable string
        if polarity == oms.IonSource.Polarity.POSITIVE:
            polarity_str = "Positive"
        elif polarity == oms.IonSource.Polarity.NEGATIVE:
            polarity_str = "Negative"
        else:
            polarity_str = "Unknown"

        polarity_list.append(polarity_str)

        cut += 1

    unique_polarity_list = list(set(polarity_list))

    if len(unique_polarity_list) == 1:
        return unique_polarity_list[0]
    else:
        return ','.join(unique_polarity_list)
