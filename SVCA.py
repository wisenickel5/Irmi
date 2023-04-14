import numpy as np
from sklearn import datasets
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# simple construct object to hold a modles weights or other stuff if we want

class IVP:

    def __init__(self, model):
        self.model = model


# this computes the linear transformtion of our vector into classifcation space R^n
def calc_Wx(W, x):
    return W.dot(x)


# data preprocessing method one
def norm_column(column):
    w = max(column)
    for i in range(0, len(column)):
        column[i] = (column[i]) / (w + .0001)
    return column


def norm_data(data):
    for i in range(0, data.shape[1]):
        data[:, i] = preprocessing.normalize([norm_column(data[:, i])])
    return data


# This is the measurement function
def prediction(P):
    maxi = 0
    for i in range(0, len(P)):
        if P[i] > P[maxi]:
            maxi = i
    return maxi


# This update function is essentially a training function, it finds the optimal transformation W
# update predictions
def update(W, x, y, a, c):
    P = prediction(calc_Wx(W, x))
    if P != y:
        for i in range(0, len(W)):
            if i != y:
                W[i, :] = -(1 / (c ** a)) * x + W[i, :]
            else:
                W[i, :] = (1 / (c ** a)) * x + W[i, :]
    return W


# algorithm body
def IVP(data, tz):
    X = data.data
    y = data.target
    le = LabelEncoder()
    uniqueY = len(np.unique(y))
    scaler = StandardScaler().fit(X)
    scaler.fit(X)
    scaler.transform(X)
    y = le.fit_transform(data.target)

    X = norm_data(X)
    X = norm_data(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=tz)

    W = np.random.uniform(1, 1, (uniqueY, len(X[0])))
    # print(W)
    for j in range(0, int(tz * 1000)):

        for i in range(0, len(X_train)):
            W = update(W, X_train[i], y_train[i], j, uniqueY)
    c = 0

    for i in range(0, len(X_test)):
        p = prediction(calc_Wx(W, X_test[i]))
        if (y_test[i] == p):
            c += 1
    return c / len(X_test)


# Driver Code.
numbers = datasets.load_digits()
cancer = datasets.load_breast_cancer()
wine = datasets.load_wine()
iris = datasets.load_iris()
c1 = 0
c2 = 0
c3 = 0
c4 = 0
fc = 0
for i in range(0, 5):
    I = IVP(iris, .5)
    w = IVP(wine, .5)
    c = IVP(cancer, .5)
    N = IVP(numbers, .8)
    if (I or w or c) < .7:
        fc += 1
    c1 += I
    c2 += w
    c3 += c
    c4 += N
print('Avg Iris:', c1 / 5, ' Avg Wine:', c2 / 5, ' Avg Cancer:', c3 / 5, ' Avg Numbers:', c4 / 5, 'fail count ',
      fc / 100)
