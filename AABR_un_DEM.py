from __future__ import print_function, division
import locale
import os
import operator
import arcpy
from arcpy import env
locale.setlocale(locale.LC_ALL,"")#sets local settings to decimals
arcpy.env.overwriteOutput = True

arcpy.CheckOutExtension("3D")# Check the extension used

# Define the input parameters
dem=arcpy.GetParameterAsText(0)
files=arcpy.GetParameterAsText(1)
interval= int(arcpy.GetParameterAsText(2))
br= arcpy.GetParameterAsText(3)

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

#get the proper br without the use of locale.atof
if '.' in br:
    brlist=br.split('.')
    brint= int(brlist[0])
    brdec= brlist[1][:2]
    if len(brdec)==2:
        brdec=int(brdec)
        br=brint+(brdec/100)
    else:
        brdec=int(brdec)
        br=brint+(brdec/10)
elif "," in br:
    brlist=br.split(',')
    brint= int(brlist[0])
    brdec= brlist[1][:2]
    if len(brdec)==2:
        brdec=int(brdec)
        br=brint+(brdec/100)
    else:
        brdec=int(brdec)
        br=brint+(brdec/10)
else:
    try:
        br=int(br)
    except:
        arcpy.AddError("The script could not read your balance ratio because it is not a number")
        quit()
print (br)

try:
    minalt= int(minimum.split('.')[0])
except:
    minalt= int(minimum.split(',')[0])
minalt=minalt-interval

desc=arcpy.Describe(dem) # Get information from the DEM
nombre=os.path.join(files,desc.baseName+".txt") # Get the name from the DEM

# Create a .txt file and populate it with the data from the Surface volume
# calculation, given the thresholds and the interval
with open(nombre,"w") as f:
    try:
        for plane in range(minalt, maxalt, interval):
            result=arcpy.SurfaceVolume_3d(dem,"", "BELOW", plane)
            print (arcpy.GetMessage(0), file=f)
            print (arcpy.GetMessage(1), file=f)
            print (arcpy.GetMessage(2), file=f)
            print (arcpy.GetMessage(3), file=f)
    except Exception as e:
        print (e.message)
    f.close


# Create a list of altitudes
list_altitudes=[]
start_altitude=minalt+(interval/2)
while start_altitude > minalt and start_altitude < maxalt:
    list_altitudes.append(start_altitude)
    start_altitude=start_altitude+interval

# Read the .txt and populate lists with the relevant data
with open(nombre, "r") as fo:
    k=fo.read() # read the words of the .txt
    s=k.replace('=',' ') # change = for _
    p=s.split() # divide the words in a list of words

    # lists to be populated
    otroindexes=[]
    segundovalor=[]
    resta=[]
    multiplicacion=[]

    # Populate otroindexes with the index number of the two words after "3D"
    for a,v in enumerate(p):
        if "3D" in v:
            otroindexes.append(a+1)#take both words after 3D (in some languages
                                    #the "Area" word and the result are interchanged
            otroindexes.append(a+2)
        else:
            pass

    # Populate segundovalor with the value of the word that corresponds to
    # the index and is not "Area"
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

# AA Calculation
    superf_total=max(segundovalor)
    resta=[int(x)-int(y) for (x,y) in zip(segundovalor[1:], segundovalor[0:])]
    multiplicacion=[int(x)*int (y) for (x,y) in zip (resta,list_altitudes)]
    finalmulti=sum(multiplicacion)
    resultAA=int(int(finalmulti)/int(superf_total))
    outlineAA=os.path.join(files,desc.baseName+"AA.shp")
    arcpy.Contour_3d(dem,outlineAA,100000,resultAA)
    arcpy.AddMessage("The ELA AA is:")
    arcpy.AddMessage(resultAA)

# AABR Calculation
    refinf=minalt
    valores_multi=[]
    valorAABR=[x*(y - refinf) for (x,y) in zip (resta, list_altitudes)]
    for valoracion in valorAABR:
        if valoracion<0:
            valores_multi.append(int (valoracion*br))
        else:
            valores_multi.append(int (valoracion))
    valorAABRfinal=sum (valores_multi)
    while valorAABRfinal > 0:
        refinf=refinf+interval
        valores_multi=[]
        valorAABR=[x*(y - refinf) for (x,y) in zip (resta, list_altitudes)]
        for valoracion in valorAABR:
            if valoracion<0:
                valores_multi.append(valoracion*br)
            else:
                valores_multi.append(valoracion)
        valorAABRfinal=sum (valores_multi)
    result= refinf-(interval/2)
    outline=os.path.join(files,desc.baseName+"AABR.shp")
    arcpy.Contour_3d(dem,outline,100000,result)
    arcpy.AddMessage("The ELA AABR is:")
    arcpy.AddMessage(result)
    fo.close # Close the .txt file

