from __future__ import print_function, division
import locale
import os
import operator
import arcpy
from arcpy import env
locale.setlocale(locale.LC_ALL,"")#sets local settings to decimals
arcpy.env.overwriteOutput = True


if arcpy.CheckExtension("3D")=="Available":
    arcpy.CheckOutExtension("3D")
else:
    print ("3D Analyst extension unavailable")

# Define the input parameters
#DEM
dem=arcpy.GetParameterAsText(0)
#Folder to store the .txt files
files=arcpy.GetParameterAsText(1)
#Altitude interval for Surface Volume calculations
interval= int(arcpy.GetParameterAsText(2))

#get the proper ratio without the use of locale.atof

def properratio(ratio):
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
    arcpy.AddMessage (ratio)
    return ratio

#Interval for AAR ratios
ratioAARandInterval= arcpy.GetParameterAsText(3)
my_list=ratioAARandInterval.split()
minratio=properratio(my_list[0])#floating of the input
minratio=int(minratio*1000)
maxratio=properratio(my_list[1])#floating of the input
maxratio=int(maxratio*1000)
intervalAAR=properratio(my_list[2])#floating of the input
intervalAAR=int(intervalAAR*1000)
maxratio=maxratio+intervalAAR#I make this to cover the last maximum ratio in range

#Interval for AABR ratios
ratioAABRandInterval= arcpy.GetParameterAsText(4)
my_list2=ratioAABRandInterval.split()
minAABR=properratio(my_list2[0])#floating of the input
minAABR=int(minAABR*1000)
maxAABR= properratio(my_list2[1])#floating of the input
maxAABR=int(maxAABR*1000)
intervalAABR=properratio(my_list2[2])#floating of the input
intervalAABR=int(intervalAABR*1000)
maxAABR=maxAABR+intervalAABR#I make this to cover the last maximum ratio in range

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


desc=arcpy.Describe(dem)
demName=os.path.join(desc.path,desc.name) # Get information from the DEM
nombre=os.path.join(files,desc.baseName+"AAR.txt")# Get the calculations .txt name from the DEM
nombreOut=os.path.join(files,desc.baseName+"_output.txt")# Get output .txt name from the DEM
nombreshp=os.path.join(files,desc.baseName+"ELAs.shp")
listELAS=[]

# Create a .txt file and populate it with the data from the Surface volume
# calculation, given the thresholds and the interval
with open(nombre,"w") as f:
    for plane in range(minalt, maxalt, interval):
        print (plane, file=f)
        try:
            arcpy.SurfaceVolume_3d(dem,"", "ABOVE", plane)
            print (arcpy.GetMessage(0), file=f)
            print (arcpy.GetMessage(1), file=f)
            print (arcpy.GetMessage(2), file=f)
            print (arcpy.GetMessage(3), file=f)
        except Exception as e:
            print (e.message)
    f.close

# Create a list of altitudes for AAR
primervalor=[]
start_altitude=minalt
while start_altitude >= minalt and start_altitude < maxalt:
    primervalor.append(start_altitude)
    start_altitude=start_altitude+interval


#Read the .txt and populate lists with the relevant data
with open(nombre, "r") as fo:
    k=fo.read()# read the words of the .txt
    s=k.replace('=',' ')# change = for a space
    p=s.split()# divide the words in a list of words

    # lists to be populated
    otroindexes=[]
    segundovalor=[]

    # Populate otroindexes with the index number of the second word after "3D"
    for a,v in enumerate(p):
        if "3D" in v:
            otroindexes.append(a+1)#take both words after 3D (in some languages
                                    #the "Area" word and the result are interchanged
            otroindexes.append(a+2)
        else:
            pass

     # Populate segundovalor with the value of the
    # word that corresponds to the index value
    for index,c in enumerate (p):
        for e in otroindexes:
            if index==e:
                try:#if there is a number take if there is "Area" pass
                    try:#both treat comma and point decimals
                        segundovalor.append(int(c.split('.')[0]))
                    except:
                        segundovalor.append(int(c.split(',')[0]))
                    break
                except:
                    pass

    # Create a dictionary with both lists
    dictionary = dict(zip(primervalor, segundovalor))
    fo.close

superf_total=max(segundovalor)# Get the total surface

#set the surface of ELA kurowski
kurowski= superf_total * 0.5

# Create a list of the altitudes whose surface is less than ELA kurowski
superf_kurowski=[]
for values in segundovalor:
    if values <= kurowski:
        superf_kurowski.append(values)
    else:
        pass

# Identify the maximum value, from which the ELA is retrieved and write to output .txt
kur=max(superf_kurowski)
for altitudes, superficies in dictionary.iteritems():
    if superficies==kur:
        elaok=altitudes + (interval/2) # the final ELA is the value in the middle of the interval
        listELAS.append(int(elaok))
        with open(nombreOut,"a") as r:
            print(("The ELA MGE is %r" %(elaok)), file=r)
            r.close

#Identify the ELA given different ratios
for ratio in range(minratio, maxratio, intervalAAR):
    ratiook= ratio/1000
    ELA=superf_total * ratiook # Get the surface above the ELA

    # Create a list of the altitudes whose surface is less than ELA
    superf_en_ELA=[]
    for values in segundovalor:
        if values <= ELA:
            superf_en_ELA.append(values)
        else:
            pass
    # Get the maximum surface value within the list
    ela=max(superf_en_ELA)

    #Get the altitude value that corresponds to the surface and write to the .txt
    for altitudes, superficies in dictionary.iteritems():
        if superficies==ela:
            elaok=altitudes + (interval/2) # the final ELA is the value in the middle of the interval
            listELAS.append(int(elaok))
            with open(nombreOut,"a") as r:
                print(("The ELA AAR at ratio %r is: %r" %(ratiook,elaok)), file=r)
                r.close
        else:
            pass

# AA Calculation
nombre=os.path.join(files,desc.baseName+"AABR.txt")#Name for the AABR .txt file
nombreOut=os.path.join(files,desc.baseName+"_output.txt")

# Create a .txt file and populate it with the data from the Surface volume
# calculation, given the thresholds and the interval, this time the calculation
#is BELOW the threshold
with open(nombre,"w") as f:
    for plane in range(minalt, maxalt, interval):
        try:
            arcpy.SurfaceVolume_3d(dem,"", "BELOW", plane)
            print (arcpy.GetMessage(0), file=f)
            print (arcpy.GetMessage(1), file=f)
            print (arcpy.GetMessage(2), file=f)
            print (arcpy.GetMessage(3), file=f)
        except Exception as e:
            print (e.message)
    f.close

# Create a list of reference altitudes
list_altitudes=[]
start_altitude=minalt+(interval/2)
while start_altitude > minalt and start_altitude < maxalt:
    list_altitudes.append(start_altitude)
    start_altitude=start_altitude+interval

with open(nombre, "r") as fe:
    k=fe.read() # read the words of the .txt
    s=k.replace('=',' ') # change = for a space
    p=s.split() # divide the words in a list of words

    # lists to be populated
    otroindexes=[]
    segundovalor=[]
    resta=[]
    multiplicacion=[]

    # Populate otroindexes with the index number of the second word after "3D"
    for a,v in enumerate(p):
        if "3D" in v:
            otroindexes.append(a+1)#take both words after 3D (in some languages
                                    #the "Area" word and the result are interchanged
            otroindexes.append(a+2)
        else:
            pass

    # Populate segundovalor with the value of the word that corresponds to
    # the index
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
    fe.close
# Open the .txt and AA calculation
with open(nombreOut,"a") as r:
    superf_total=max(segundovalor)
    resta=[int(x)-int(y) for (x,y) in zip(segundovalor[1:], segundovalor[0:])]
    multiplicacion=[int(x)*int (y) for (x,y) in zip (resta,list_altitudes)]
    finalmulti=sum(multiplicacion)
    resultAA=int(int(finalmulti)/int(superf_total))
    listELAS.append(resultAA)
    print(("The ELA AA is: %r" %(resultAA)), file=r)

    # AABR Calculation for the ratios in range
    for ratios in range(minAABR, maxAABR, intervalAABR):
        br= ratios/1000
        refinf=minalt #first trial altitude
        valores_multi=[]
        valorAABR=[x*(y - refinf) for (x,y) in zip (resta, list_altitudes)]
        for valoracion in valorAABR:
            if valoracion<0:
                valores_multi.append(int (valoracion*br)) #Balance ratio is multiplied
            #only if result is negative
            else:
                valores_multi.append(int (valoracion))
        valorAABRfinal=sum (valores_multi)
        while valorAABRfinal > 0:#this loop works until find a negative result in
        #valorAABRfinal, then the value stored in refinf marks the upper limit
        #of the belt that holds the ELA
            refinf=refinf+interval
            valores_multi=[]
            valorAABR=[x*(y - refinf) for (x,y) in zip (resta, list_altitudes)]
            for valoracion in valorAABR:
                if valoracion<0:
                    valores_multi.append(valoracion*br)
                else:
                    valores_multi.append(valoracion)
            valorAABRfinal=sum (valores_multi)
        result= refinf-(interval/2) # the final ELA is the mid value of the belt
        listELAS.append(int(result))
        print(("The ELA AABR at ratio %r is: %r" %(br,result)), file=r)
    r.close # Close the .txt file
arcpy.AddMessage (listELAS)
arcpy.ContourList_3d(dem, nombreshp, listELAS)

