from __future__ import print_function, division
import locale
import os
import operator
import arcpy
from arcpy import env
locale.setlocale(locale.LC_ALL,"")#sets local settings to decimals
arcpy.env.overwriteOutput = True

# Check the extensions used
arcpy.CheckOutExtension("3D")

# Define the input parameters
dem=arcpy.GetParameterAsText(0)
files=arcpy.GetParameterAsText(1)
interval= int(arcpy.GetParameterAsText(2))
ratio= arcpy.GetParameterAsText(3)

#Maximum and minimum value of DEM
upper=arcpy.GetRasterProperties_management(dem,"MAXIMUM")
maximum=upper.getOutput(0)
lower=arcpy.GetRasterProperties_management(dem,"MINIMUM")
minimum=lower.getOutput(0)

#both treat comma and point decimals
try:
    maxalt= int(maximum.split('.')[0])
except:
    maxalt= int(maximum.split(',')[0])
maxalt=maxalt+interval

try:
    minalt= int(minimum.split('.')[0])
except:
    minalt= int(minimum.split(',')[0])
minalt=minalt-interval

#get the proper ratio without the use of locale.atof

if '.' in ratio:
    ratiolist=ratio.split('.')
    ratioint= int(ratiolist[0])
    ratiodec= ratiolist[1][:2]
    if len(ratiodec)==2:
        ratiodec=int(ratiodec)
        ratio=ratioint+(ratiodec/100)
    else:
        ratiodec=int(ratiodec)
        ratio=ratioint+(ratiodec/10)
elif "," in ratio:
    ratiolist=ratio.split(',')
    ratioint= int(ratiolist[0])
    ratiodec= ratiolist[1][:2]
    if len(ratiodec)==2:
        ratiodec=int(ratiodec)
        ratio=ratioint+(ratiodec/100)
    else:
        ratiodec=int(ratiodec)
        ratio=ratioint+(ratiodec/10)
else:
    try:
        ratio=int(ratio)
    except:
        arcpy.AddError("The script could not read your ratio because it is not a number")
        quit()
print (ratio)
desc=arcpy.Describe(dem) # Get information from the DEM
nombre=os.path.join(files,desc.baseName+".txt") # Get the name from the DEM

# Create a .txt file and populate it with the data from the Surface volume
# calculation, given the thresholds and the interval
with open(nombre,"w") as f:
    for plane in range(minalt, maxalt, interval):
        try:
            result=arcpy.SurfaceVolume_3d(dem,"", "ABOVE", plane)
            print (arcpy.GetMessage(0), file=f)
            print (arcpy.GetMessage(1), file=f)
            print (arcpy.GetMessage(2), file=f)
            print (arcpy.GetMessage(3), file=f)
        except Exception as e:
            print (e.message)
    f.close

# Create list of altitudes and populate primervalor
primervalor=[]
start_altitude=minalt
while start_altitude >= minalt and start_altitude < maxalt:
    primervalor.append(start_altitude)
    start_altitude=start_altitude+interval

# Read the .txt and populate lists with the relevant data
with open(nombre, "r") as fo:
    k=fo.read() #read the words of the .txt
    s=k.replace('=',' ') #change = for _
    p=s.split() #divide the words in a list of words

    #lists to be populated
    otroindexes=[]
    segundovalor=[]


    # Populate otroindexes with the index number of the two words after "3D"
    for a,v in enumerate(p):
        if "3D" in v:
            otroindexes.append(a+1)#take both words after 3D (in some languages
                                #the "Area" word and the result are interchanged
            otroindexes.append(a+2)
        else:
            pass

    # Populate segundovalor with the value of the word that corresponds
    # to the index value in otrosindexes and is not "Area"
    for index,c in enumerate (p):
        for e in otroindexes:
            if index==e:
                try:
                    try:#both treat comma and point decimals
                        segundovalor.append(int(c.split('.')[0]))
                    except:
                        segundovalor.append(int(c.split(',')[0]))
                    break
                except:
                    pass
    # Create a dictionary with both lists
    dictionary = dict(zip(primervalor, segundovalor))

    superf_total=max(segundovalor) # Get the total surface
    ELA=superf_total * ratio # Get the surface above the ELA
    kurowski= superf_total * 0.5

# Create a list of the altitudes whose surface is less than ELA
    superf_en_ELA=[]
    superf_kurowski=[]
    for values in segundovalor:
        if values <= ELA and values<= kurowski:
            superf_en_ELA.append(values)
            superf_kurowski.append(values)
        elif values <= ELA and values> kurowski:
            superf_en_ELA.append(values)
        elif values > ELA and values<= kurowski:
            superf_kurowski.append(values)
        else:
            pass

# Get the maximum surface value within the list
    ela=max(superf_en_ELA)
    kur=max(superf_kurowski)

#Get the altitude value that corresponds to the surface
    for altitudes, superficies in dictionary.iteritems():
        if superficies==ela:
            elaok=altitudes + (interval/2)
            outline=os.path.join(files,desc.baseName+"AAR.shp")
            arcpy.Contour_3d(dem,outline,100000,elaok)
            arcpy.AddMessage("The ELA AAR is:")
            arcpy.AddMessage(elaok)
            break
    for altitudes, superficies in dictionary.iteritems():
        if superficies==kur:
            elaok=altitudes + (interval/2)
            outline=os.path.join(files,desc.baseName+"MGE.shp")
            arcpy.Contour_3d(dem,outline,100000,elaok)
            arcpy.AddMessage("The ELA MGE is:")
            arcpy.AddMessage(elaok)
            break
    fo.close # Close the .txt file

