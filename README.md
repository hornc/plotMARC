# plotMARC

## Basic usage

From a directory containing one or more binary [MARC21](https://www.loc.gov/marc/bibliographic/) format for bibliographic data files (with extension `.mrc`)
representing a bibliographic collection, run:

    ./plotMARC.py
    
The script will process the MARC files using [pymarc](https://gitlab.com/pymarc/pymarc),
and produce a single `<directoryname>.png` image showing a 3-way Venn diagram displaying the number of records with the following bibliographic identifiers:
  
  * ISBN
  * OCN ([OCLC](https://www.oclc.org/) number)
  * LCCN ([Library of Congress](https://loc.gov/) number)
  
  and a histogram showing the publication dates in the bib records.
  
  ## [Requirements](requirements.txt)
 
  * [pymarc](https://gitlab.com/pymarc/pymarc)
  * [matplotlib](https://matplotlib.org/)
  * [matplotlib_venn](https://github.com/konstantint/matplotlib-venn)
 
  Install these using pip:
 
     pip install -r requirements.txt
 
