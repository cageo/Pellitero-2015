from __future__ import print_function, division
import locale
import os
import numpy
import arcpy
from arcpy import env
locale.setlocale(locale.LC_ALL,"")#sets local settings to decimals
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("3D")

#Workspace
jj=arcpy.env.workspace=arcpy.GetParameterAsText(0)
#Altitude interval for Surface Volume calculations
interval= int(arcpy.GetParameterAsText(1))

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
ratioAARandInterval= arcpy.GetParameterAsText(2)
my_list=ratioAARandInterval.split()
minratio=properratio(my_list[0])#floating of the input
minratio=int(minratio*1000)
maxratio=properratio(my_list[1])#floating of the input
maxratio=int(maxratio*1000)
intervalAAR=properratio(my_list[2])#floating of the input
intervalAAR=int(intervalAAR*1000)
maxratio=maxratio+intervalAAR#I make this to cover the last maximum ratio in range

#Interval for AABR ratios
ratioAABRandInterval= arcpy.GetParameterAsText(3)
my_list2=ratioAABRandInterval.split()
minAABR=properratio(my_list2[0])#floating of the input
minAABR=int(minAABR*1000)
maxAABR= properratio(my_list2[1])#floating of the input
maxAABR=int(maxAABR*1000)
intervalAABR=properratio(my_list2[2])#floating of the input
intervalAABR=int(intervalAABR*1000)
maxAABR=maxAABR+intervalAABR#I make this to cover the last maximum ratio in range


rasters=arcpy.ListDatasets("*","Raster")#Create a list of rasters
nombreOut=os.path.join(jj,"ELA_values_AAR_and_AABR.txt")# Get output .txt file

#create lists for a dictionary for the Osmaston (2006) ELA procedure
#one dictionary for AAR and other for AABR
osmaAllAAR=[]
osmaAllAABR=[]

# Create a .txt file per raster and populate it with the data from the
#Surface volume calculation, given the thresholds and the interval
for raster in rasters:
    describ=arcpy.Describe(raster)
    #Get the maximum and minimum altitude values
    upper=arcpy.GetRasterProperties_management(raster,"MAXIMUM")
    maximum=upper.getOutput(0)
    lower=arcpy.GetRasterProperties_management(raster,"MINIMUM")
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

    # Create list of altitudes for AAR
    primervalor=[]
    start_altitude=minalt
    while start_altitude >= minalt and start_altitude < maxalt:
        primervalor.append(start_altitude)
        start_altitude=start_altitude+interval

    #create lists for dictionary of ELA values on this raster for the Osmaston (2006)
    osmaAARratios=[]
    osmaAABRratios=[]
    osmaAARvalues=[]
    osmaAABRvalues=[]

    demName=os.path.join(jj,raster) # DEM name
    AABRfile=os.path.join(jj,describ.baseName+"below.txt")# AABR results .txt path
    AARfile=os.path.join(jj,describ.baseName+"above.txt")# AAR results .txt path
    nombreshp=os.path.join(jj,describ.baseName+"ELAs.shp") #name of ELA resulting shapefile
    listELAS=[] #list of ELAs that will define the Contour List tool

    #AAR calculation
    #Make the Surface Volume calculations
    with open(AARfile,"w") as d:
        for plane in range(minalt, maxalt, interval):
            try:
                arcpy.SurfaceVolume_3d(demName,"", "ABOVE", plane)
                print (arcpy.GetMessage(0), file=d)
                print (arcpy.GetMessage(1), file=d)
                print (arcpy.GetMessage(2), file=d)
                print (arcpy.GetMessage(3), file=d)
            except Exception as e:
                print (e.message)
        d.close

    #Read the .txt and populate lists with the relevant data
    with open(AARfile, "r") as fr:
        k=fr.read()# read the words of the .txt
        s=k.replace('=',' ')# change = for a space
        p=s.split()# divide the words in a list of words
        # lists to be populated
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
        fr.close

    superf_total=max(segundovalor)# Get the total surface

    #Identify the ELA given different ratios
    with open(nombreOut,"a") as r:
        print ("Values for raster %s"%raster, file=r)
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
                    print(("The ELA AAR at ratio %r is: %r" %(ratiook,altitudes)), file=r)
                    osmaAARratios.append(ratiook)
                    osmaAARvalues.append(altitudes)
                else:
                    pass

        kurowski=superf_total * 0.5 # Get the surface above the ELA
        superf_kurowski=[]
        for values in segundovalor:
            if values <= kurowski:
                superf_kurowski.append(values)
            else:
                pass
            # Get the maximum surface value within the list
        kur=max(superf_kurowski)
            #Get the altitude value that corresponds to the surface and write to the .txt
        for altitudes, superficies in dictionary.iteritems():
            if superficies==kur:
                elaok=altitudes + (interval/2) # the final ELA is the value in the middle of the interval
                listELAS.append(int(elaok))
                print(("The ELA MGE is: %r" %(altitudes)), file=r)
            else:
                pass
        r.close

    #AABR calulation
    # List of reference values for AABR calculations
    lista_altitudes=[]
    altura_inicial=minalt+(interval/2)
    while altura_inicial > minalt and altura_inicial < maxalt:
        lista_altitudes.append(altura_inicial)
        altura_inicial=altura_inicial+interval
    # Create a .txt file and populate it with the data from the Surface volume
    # calculation, given the thresholds and the interval, this time the calculation
    #is BELOW the threshold
    plane=minalt
    with open(AABRfile,"w") as f:
        while plane <=maxalt:
            try:
                arcpy.SurfaceVolume_3d(demName,"", "BELOW", plane)
                print (arcpy.GetMessage(0), file=f)
                print (arcpy.GetMessage(1), file=f)
                print (arcpy.GetMessage(2), file=f)
                print (arcpy.GetMessage(3), file=f)
            except Exception as e:
                print (e.message)
            plane= plane+interval
        f.close
    #Read the .txt and populate lists with the relevant data
    with open (AABRfile,"r") as fbis:
        k=fbis.read()# read the words of the .txt
        s=k.replace('=',' ')# change = for a space
        p=s.split()# divide the words in a list of words
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
        fbis.close
    # Open the results .txt and AA calculation
    with open(nombreOut,"a") as r:
        superf_total=max(segundovalor)
        resta=[int(x)-int(y) for (x,y) in zip(segundovalor[1:], segundovalor[0:])]
        multiplicacion=[int(x)*int (y) for (x,y) in zip (resta,lista_altitudes)]
        finalmulti=sum(multiplicacion)
        resultAA=int(int(finalmulti)/int(superf_total))
        listELAS.append(resultAA)
        print(("The ELA AA is: %r" %(resultAA)), file=r)
        #AABR calculation for ratios in range
        for ratio in range(minAABR, maxAABR, intervalAABR):
            br= ratio/1000
            refinf=minalt #first trial altitude
            valores_multi=[]
            valorAABR=[x*(y - refinf) for (x,y) in zip (resta, lista_altitudes)]
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
                valorAABR=[x*(y - refinf) for (x,y) in zip (resta, lista_altitudes)]
                for valoracion in valorAABR:
                    if valoracion<0:
                        valores_multi.append(valoracion*br)
                    else:
                        valores_multi.append(valoracion)
                valorAABRfinal=sum (valores_multi)
            result= refinf-(interval/2) # the final ELA is the mid value of the belt
            listELAS.append(int(result))
            print(("The ELA AABR at ratio %r is: %r" %(br,result)), file=r)
            osmaAABRratios.append(br)
            osmaAABRvalues.append(result)
        r.close# Close the .txt file
    arcpy.ContourList_3d(raster, nombreshp, listELAS)

    #Create the dictionary dor this raster and populate the whole list
    osmaAAR= dict(zip(osmaAARratios, osmaAARvalues))
    osmaAllAAR.append(osmaAAR)
    osmaAABR= dict (zip(osmaAABRratios,osmaAABRvalues))
    osmaAllAABR.append(osmaAABR)

#Calculations for Osmaston (2006) best ELA implementation for AAR and AABR

averageAAR=[]
stdAAR=[]
ratiosAAR=[]
averageAABR=[]
stdAABR=[]
ratiosAABR=[]


for rat in range(minratio, maxratio, intervalAAR):
    goodratio=rat/1000
    ratiosAAR.append(goodratio)
    ela=[]
    for value in osmaAllAAR:
        ela.append(value.get(goodratio))
    media=numpy.mean(ela)
    avr=numpy.std(ela)
    averageAAR.append(media)
    stdAAR.append(avr)

for rat in range(minAABR, maxAABR, intervalAABR):
    goodratio=rat/1000
    ratiosAABR.append(goodratio)
    ela=[]
    for value in osmaAllAABR:
        #get the value from the dictionaries with key equal to the ratio
        ela.append(value.get(goodratio))
    media=numpy.mean(ela)
    avr=numpy.std(ela)
    averageAABR.append(media)
    stdAABR.append(avr)

minstdAAR= min (stdAAR)
minstdAABR= min (stdAABR)

#get the index of the minimum value in the standard deviation list
indexAAR=stdAAR.index(minstdAAR)
indexAABR=stdAABR.index(minstdAABR)

with open(nombreOut,"a") as last:
    print((("The minimum standard deviation ELA for AAR method is %r meters at a ratio of %r and an average of %r meters" %(int(minstdAAR),(ratiosAAR[indexAAR]),(averageAAR[indexAAR])))),file=last)
    print((("The minimum standard deviation ELA for AABR method is %r meters at a ratio of %r and an average of %r meters" %(int(minstdAABR),(ratiosAABR[indexAABR]),(averageAABR[indexAABR])))),file=last)
    print (("For Osmaston (2006) ELA retrieval, user is advised to assume that all glaciers included are coetaneous"), file=last)
