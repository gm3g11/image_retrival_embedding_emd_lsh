from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import argparse
# import utils
import cv2
import random
import numpy as np
import pickle
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.image as mpimg
import os
import math
# import pylshbox
# import libpylshbox
import heapq

try:
    os.remove("./database/.DS_Store")
    os.remove("./query/.DS_Store")
except OSError:
    pass

Hash_count = 0

hasSeenImageName = {}

def Maphash(l):
    global Hash_count
    Hash_count += 1
    print ("Vector " , Hash_count," Getting started to hashed and reduced")
    StartSliceIndex = 0
    StopSliceIndex=0
    HashedResults = []
    while StopSliceIndex < len(l):
        StopSliceIndex = min(StartSliceIndex+1000,len(l))
        l_temp = l[StartSliceIndex:StopSliceIndex]
        StartSliceIndex = StartSliceIndex +1000
        l_temp = hash(tuple(l_temp))%32416190071
        HashedResults.append(l_temp)
    print ("Done getting hashed and reduced size")
    return HashedResults

'''
    A formula to determine the id of starting point of a left top most corner
    of a cube
'''

def formula(cubeX,cubeY,cubeZ,sidelen,xshift,yshift,zshift):
    xc = math.ceil(((xshift%sidelen) + cubeX + 1)*1.0/sidelen)
    yc = math.ceil(((yshift%sidelen) + cubeY + 1)*1.0/sidelen)
    zc = math.ceil(((zshift%sidelen) + cubeZ + 1)*1.0/sidelen)
    yd = math.ceil((256+yshift%sidelen)*1.0/sidelen)
    zd = math.ceil((256+zshift%sidelen)*1.0/sidelen)
    xd = math.ceil((256+xshift%sidelen)*1.0/sidelen)
    offset = 0
    for side in range(0,int(math.log(sidelen,2))):
        yp = math.ceil((256+yshift%(2**side))*1.0/((2**side)))
        zp = math.ceil((256+zshift%(2**side))*1.0/(2**side))
        xp = math.ceil((256+xshift%(2**side))*1.0/(2**side))
        offset += xp*yp*zp
    #offset = int(math.log(sidelen,2))*xd*yd*zd
    return int(offset + (xc - 1)*yd*zd + (yc-1)*zd + zc - 1)

'''
    Gets the image and filename from a particular folder 'folder'
    and stores the rgb values of that image and its name in a vector
'''

def load_images(folder):
    images = []
    imageFileNames = []
    for filename in os.listdir(folder):
        img = mpimg.imread(os.path.join(folder, filename))
        if img is not None:
            imageFileNames.append(filename)
            images.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return images,imageFileNames

'''
    creates a mapping from image to number of clusters
    where its silhoute score of optimum
    and clusters that image with those number of clusters
    Another approach could be to store clt objects also
    in a file , but it all depends on tradeoff
'''

def createMappingOfImageToNClusters():
    fil = open('database.txt','r')
    fileClusterMap = {}
    #for dataset images
    for line in fil:
        fileClusterMap[line.split(' ')[0]] = int(line.split(' ')[1])
    #for query images
    fil = open('query.txt','r')
    for line in fil:
        fileClusterMap[line.split(' ')[0]] = int(line.split(' ')[1])
    return fileClusterMap

'''
    gets some of the stats as mentioned in the paper like
    average number of clusters per image, but this can be changed on
    the basis of how and when elbow point is chosen
    or other approaches like density based clustering may solve the issue
'''
def getStats(fileClusterMap):
    meanNumberOfClusters = np.mean(np.array(list(fileClusterMap.values())))
    print ("Average clusters per image: ",meanNumberOfClusters)
    return

'''
    This determines the randomshifting of grids
'''
def getRandomShifts():
    return (int(random.uniform(0,255)),int(random.uniform(0,255)),int(random.uniform(0,255)))

'''
    Get the flabel weights and ImageClt objects for all images
'''
def getFlablesAndImageClt(images,imageFileNames,fileClusterMap):
    imageCount = 0
    flabels =[]
    #store clt(object) of every image in this:
    ImgClt = {}
    global hasSeenImageName
    for image in images:
        if imageFileNames[imageCount] in hasSeenImageName.keys():
            ImgClt[imageCount] = hasSeenImageName[imageFileNames[imageCount]]
            labelc = [0]*(len(ImgClt[imageCount].cluster_centers_))
            for i in ImgClt[imageCount].labels_:
                labelc[i]+=1
            flabels.append(labelc)
            print (imageFileNames[imageCount],'n_cluster:',len(ImgClt[imageCount].cluster_centers_),\
            'imageCount:',imageCount,'/',len(images))
            imageCount+=1
            continue
        image = image.reshape((image.shape[0] * image.shape[1], 3))
        if imageFileNames[imageCount] not in fileClusterMap.keys():
            print (imageFileNames[imageCount] ," doen't have a mapping in pre processed data")
            imageCount+=1
            continue
        n_cluster = fileClusterMap[imageFileNames[imageCount]]
        ImgClt[imageCount] = KMeans(n_clusters = n_cluster)
        ImgClt[imageCount].fit(image)
        print (imageFileNames[imageCount],'n_cluster:',n_cluster,'imageCount:',imageCount,'/',len(images))
        #finding the approximate diameter

        labelc = [0]*(n_cluster)
        for i in ImgClt[imageCount].labels_:
            labelc[i]+=1
        flabels.append(labelc)
        hasSeenImageName[imageFileNames[imageCount]] = ImgClt[imageCount]
        imageCount+=1
    return flabels,ImgClt

'''
    Get Appended list after embedding as mentioned in the paper
    and get the number of points of each image in a particular cube
'''
def getAppendedVeList(images,ImgClt,xshift,yshift,zshift):
    imageCount = 0
    velist = []
    for image in images:
        if imageFileNames[imageCount] not in fileClusterMap.keys():
            print (imageFileNames[imageCount] ," doen't have a mapping in pre processed data")
            imageCount+=1
            continue
        sidelen = 1
        mappingPointsToCube = [0]*(3*(10**7))
        while sidelen<=255:
            for points in ImgClt[imageCount].cluster_centers_:
                [x,y,z] = points
                CubeX = int(x/sidelen)*sidelen + (sidelen-(xshift%sidelen))%sidelen
                CubeY = int(y/sidelen)*sidelen + (sidelen-(yshift%sidelen))%sidelen
                CubeZ = int(z/sidelen)*sidelen + (sidelen-(zshift%sidelen))%sidelen
                mappingPointsToCube[formula(CubeX,CubeY,CubeZ,sidelen,xshift,yshift,zshift)]+=(sidelen)
            sidelen*=2
        mappingPointsHash = Maphash(mappingPointsToCube)
        velist.append(mappingPointsHash)
        imageCount+=1
    return velist


#load dataset images
images,imageFileNames = load_images("./database/")

# #load query images
queryImages, queryImageNames = load_images("./query/")

# #get mapping
fileClusterMap = createMappingOfImageToNClusters()
#
# #get average number of cluster per image
getStats(fileClusterMap)

#get flables and ImgClt
#flabels,ImgClt = getFlablesAndImageClt(images,imageFileNames,fileClusterMap)
if os.path.exists("flabels.txt"):
    with open("flabels.txt", "rb") as fq:  # Pickling
        flabels=pickle.load(fq)
    with open("ImgClt.txt", "rb") as icq:  # Pickling
        ImgClt=pickle.load(icq)
else:
    flabels,ImgClt = getFlablesAndImageClt(images,imageFileNames,fileClusterMap)
    with open("flabels.txt", "wb") as fq:  # Pickling
        pickle.dump(flabels, fq)
    with open("ImgClt.txt", "wb") as icq:  # Pickling
        pickle.dump(ImgClt, icq)

#get flables and ImgClt for query images
if os.path.exists("flabelsQuery.txt"):
    with open("flabelsQuery.txt", "rb") as fq:  # Pickling
        flabelsQuery=pickle.load(fq)
    with open("ImgCltQuery.txt", "rb") as icq:  # Pickling
        ImgCltQuery=pickle.load(icq)

else:
    flabelsQuery,ImgCltQuery = getFlablesAndImageClt(queryImages,queryImageNames,fileClusterMap)
    with open("flabelsQuery.txt", "wb") as fq:  # Pickling
        pickle.dump(flabelsQuery, fq)
    with open("ImgCltQuery.txt", "wb") as icq:  # Pickling
        pickle.dump(ImgCltQuery, icq)




if os.path.exists("velist.txt"):
    with open("velist.txt", "rb") as fq:  # Pickling
        velist=pickle.load(fq)
    with open("velistQuery.txt", "rb") as icq:  # Pickling
        velistQuery=pickle.load(icq)
else:
    # this contains the vector generated as discussed in paper after embedding
    velist = []

    # finding the random shift for each axis
    (xshift, yshift, zshift) = getRandomShifts()

    print("Done Creating Cube Embedding, moving on to finding number of points in each cube")

    velist = getAppendedVeList(images, ImgClt, xshift, yshift, zshift)

    velistQuery = getAppendedVeList(queryImages, ImgCltQuery, xshift, yshift, zshift)
    with open("velist.txt", "wb") as fq:  # Pickling
        pickle.dump(velist, fq)
    with open("velistQuery.txt", "wb") as icq:  # Pickling
        pickle.dump(velistQuery, icq)




print ("Embedding for each image complete.! check once for speed")

# '''
#     Finally get f(p)-f(q) for each query image
#     Uncomment this to test
# '''


queryImageCount = 0
retrival={}
for queryImageVector in velistQuery:
    imageCount = 0
    dist=[]
    for imageVector in velist:
        l1=np.sum(np.absolute(np.subtract(np.array(imageVector),np.array(queryImageVector))))
        print ('diff between ',queryImageNames[queryImageCount], 'and',imageFileNames[imageCount],'is',l1)
        dist.append(l1)
        imageCount+=1
    top5_index=list(map(dist.index,heapq.nsmallest(5,dist)))
    for index in top5_index:
        query_img=queryImageNames[queryImageCount]
        retrival_img=imageFileNames[index]
        if query_img not in retrival:
            retrival[query_img]=[retrival_img]
        else:
            retrival[query_img].append(retrival_img)


    queryImageCount+=1
retrival_file = open("retrival.pkl", "wb")
pickle.dump(retrival , retrival_file )
retrival_file .close()


# '''
#     LSH
# '''
# psdL1_mat = libpylshbox.psdlsh()
# psdL1_mat.init_mat(velist, '', 20, 4, 1, 5)
# queryImageCount = 0
# for queryImageVector in velistQuery:
#     result = psdL1_mat.query(queryImageVector, 2, 10)
#     indices, dists = result[0], result[1]
#     for i in range(len(indices)):
#         print ("for query image: ",queryImageNames[queryImageCount]," datesetImage",imageFileNames[indices[i]], '\t', dists[i])
#     queryImageCount+=1