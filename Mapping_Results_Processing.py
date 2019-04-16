#!/usr/bin/env python3

#Import required libraries
import pandas as pd
import sys

##MISSING: ARGPARSE!! command line arguments (mapstat file / res file / genus or specie option / total reads / minimal number of barcodes)
#Total read count from the sample - ask it as an input? 
total_read_count = 155751012

##Data files import as a data frame: 
#MAPSTAT file: 
mapstat_infile = pd.read_csv("Tomato_Mapping.mapstat", sep = "\t", skiprows = [1,5], usecols = ["# refSequence", "readCount"])

#RES file: 
res_infile = pd.read_csv("Tomato_IBol.res", sep = "\t", usecols = ["#Template", "Score", "Template_Coverage", "Depth"])

#Merge MAPSTAT and RES dataframes: 
merged_data = pd.merge(res_infile, mapstat_infile, how = 'outer', left_on='#Template', right_on='# refSequence')
merged_data = merged_data.drop("#Template", axis = 1)

##Data manipulation: 
#Clean the data from low quality hits: 
clean_data = merged_data[(merged_data["Template_Coverage"])>=50]

#Extract the description and add their labels: 
description = clean_data["# refSequence"]

barcode_add = list()
genus_add = list()


##HERE IT MUST BE MODIFIED TO INCLUDE GENUS / SPECIE GROUPING!!
#Iterate over the raw results to extract relevant data regarding the genus/specie and barcodes: 
for label in description: 
    col = label.split("|")
    genus = col[1]
       
    #Update genus and barcodes list:
    genus_add.append(genus)
    barcode_add.append(col[2])

#Update dataframe with the extracted information: 
clean_data["Label"]=genus_add
clean_data["Barcode"]=barcode_add
mod_data = clean_data.drop("# refSequence",axis=1)

#Sort and group data entries by genus/specie: 
grouped_data = mod_data.sort_values(by=["Label", "Barcode"]).groupby(["Label", "Barcode"], as_index = False).agg("sum")

#Count the barcodes identified from each genus/specie: 
count_barcodes = dict()
total_species = grouped_data["Label"]

for specie in total_species:
    if specie in count_barcodes:
        count_barcodes[specie] += 1
    else: 
        count_barcodes[specie] = 1

#Create list for the barcode count: 
final_barcode_count = list() 

for specie in total_species: 
    final_barcode_count.append(count_barcodes.get(specie))

grouped_data["Number Barcodes"] = final_barcode_count

##Final aggregation by genus and specie, including all their identified barcodes: 
#Aggregation dict for the last grouping function: 
aggregation = {'Score':'sum', 'Template_Coverage':'sum', 'Depth':'sum', 'readCount': 'sum', 'Number Barcodes' : 'mean'}

#Group the data:
data_by_genus = grouped_data.sort_values(by=["Label"]).groupby(["Label"]).agg(aggregation)

#Exclude data entries with only one identified barcode to avoid false positives:
data_by_genus_no_single_barcode = data_by_genus[(data_by_genus["Number Barcodes"])>1]

#Obtain the relative read count and sort: 
relative_read_abundance = [x / total_read_count for x in data_by_genus_no_single_barcode["readCount"]]
data_by_genus_no_single_barcode["Relative read abundance"] = relative_read_abundance
final_results = data_by_genus_no_single_barcode.sort_values(by=["Relative read abundance"], ascending = False)

##MISSING: WRITTING OUTPUT FILE BASED ON final_results DATAFRAME