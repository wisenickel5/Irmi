import numpy as np
from sklearn import preprocessing
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


# simple construct object to hold a models weights or other stuff if we want

class MODEL:
    def __init__(self, model):
        self.model = model


# this computes the linear transformation of our vector into classification space R^n
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
    X = list()
    y = list()
    for i in range(0, len(data)):
        temp = list()
        for j in range(0, len(data[0])):
            if j < len(data[0]) - 1:
                temp.append(data[i][j])
            else:
                y.append(data[i][j])
            X.append(temp)
    X = np.array(X)
    y = np.array(y)
    le = LabelEncoder()
    uniqueY = len(np.unique(y))
    scaler = StandardScaler().fit(X)
    scaler.fit(X)
    scaler.transform(X)
    X = norm_data(X)
    X = norm_data(X)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=tz)

    W = np.random.uniform(1, 1, (uniqueY, len(X[0])))

    for j in range(0, int(tz * 1000)):

        for i in range(0, len(X_train)):
            W = update(W, X_train[i], y_train[i], j, uniqueY)
    c = 0
    potential_songs = list()
    for i in range(0, len(X)):
        p = prediction(calc_Wx(W, X))
        if p == 1:
            potential_songs.append(X)
        if y[i] == p:
            c += 1
    return c / len(X_test), W, potential_songs
