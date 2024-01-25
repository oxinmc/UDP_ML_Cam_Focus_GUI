import numpy as np  
from sklearn import preprocessing, svm  
from sklearn.preprocessing import StandardScaler  
  
a=0  
b=0  
  
sharp_laplaces = []  
blurry_laplaces = []  
y = []  
  
with open('ML_Data.txt', 'r') as file:  
      for line in file:  
        h,s,t = line.partition('\t')  
        if h == 'Sharp':  
            h,s,t = t.partition('\t')  
            sharp_laplaces.append((h,t))  
            #sharp_laplaces.append(t)  
            a = a+1  
              
        elif h == 'Blurry':  
            h,s,t = t.partition('\t')  
            blurry_laplaces.append((h,t))  
            #blurry_laplaces.append(t)  
            b = b+1  
  
y = np.concatenate((np.ones((a, )), np.zeros((b, ))), axis=0)  
laplaces = np.concatenate((np.array(sharp_laplaces), np.array(blurry_laplaces)), axis=0)  
  
laplaces = preprocessing.scale(laplaces)  
  
  
clf = svm.SVC(kernel='linear', C=1, probability=True)  
clf.fit(laplaces, y)  
  
import pickle  
  
# save  
with open('focus_model.pkl','wb') as f:  
    pickle.dump(clf,f)  
