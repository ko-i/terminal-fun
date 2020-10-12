import numpy as np

def loadDataSet(filename):
    dataMatrix = []
    labelMatrix = []
    with open(filename, 'r') as fr:
        for line in fr.readlines():
            lineArr = line.strip().split('\t')
            dataMatrix.append([float(lineArr[0]), float(lineArr[1])])
            labelMatrix.append(float(lineArr[2]))
    
    return dataMatrix, labelMatrix

def selectJrand(i, m):
    j = int(np.random.uniform(0, m))
    return j

def clipAlpha(aj, H, L):
    if aj > H:
        aj = H
    if aj < L:
        aj = L

    return aj

def smoSimple(dataMatIn, classLabels, C, toler, maxIter):
    dataMatrix = np.mat(dataMatIn)
    labelMatrix = np.mat(classLabels).transpose()
    b = 0
    m, n = np.shape(dataMatrix)
    alphas = np.mat(np.zeros((m, 1)))
    iter = 0
    while iter < maxIter:
        alphaPairsChanged = 0
        for i in range(m):
            fXi = float(np.multiply(alphas, labelMatrix).T * (dataMatrix * dataMatrix[i, :].T)) + b
            Ei = fXi - float(labelMatrix[i])

            if ((labelMatrix[i] * Ei < -toler) and (alphas[i] < C)) or ((labelMatrix[i] * Ei > toler) and (alphas[i] > 0)):
                j = selectJrand(i, m)
                fXj = float(np.multiply(alphas, labelMatrix).T * (dataMatrix * dataMatrix[j, :].T)) + b
                Ej = fXj - float(labelMatrix[j])
                alphaIOld = alphas[i].copy()
                alphaJOld = alphas[j].copy()

                if labelMatrix[i] != labelMatrix[j]:
                    L = max(0, alphas[j] - alphas[i])
                    H = min(C, C + alphas[j] - alphas[i])
                else:
                    L = max(0, alphas[i] + alphas[j] - C)
                    H = min(C, alphas[i] + alphas[j])
                
                if L == H:
                    # print('L == H')
                    continue

                eta = 2.0 * dataMatrix[i, :] * dataMatrix[j, :].T - dataMatrix[i, :] * dataMatrix[i, :].T - dataMatrix[j, :] * dataMatrix[j, :].T
                if eta >= 0:
                    # print('eta >= 0')
                    continue

                alphas[j] -= labelMatrix[j] * (Ei - Ej) / eta
                alphas[j] = clipAlpha(alphas[j], H, L)

                if np.abs(alphas[j] - alphaJOld) < 0.00001:
                    # print('j not moving enough')
                    continue

                alphas[i] += labelMatrix[j] * labelMatrix[i] * (alphaJOld - alphas[j])
                b1 = b - Ei - labelMatrix[i] * (alphas[i] - alphaIOld) * dataMatrix[i, :] * dataMatrix[i, :].T - labelMatrix[j] * (alphas[j] - alphaJOld) * dataMatrix[i, :] * dataMatrix[j, :].T
                b2 = b - Ej - labelMatrix[i] * (alphas[i] - alphaIOld) * dataMatrix[i, :] * dataMatrix[j, :].T - labelMatrix[j] * (alphas[j] - alphaJOld) * dataMatrix[j, :] * dataMatrix[j, :].T

                if (0 < alphas[i]) and (C > alphas[i]):
                    b = b1
                elif (0 < alphas[j]) and (C > alphas[j]):
                    b = b2
                else:
                    b = (b1 + b2) / 2.0
                
                alphaPairsChanged += 1
                # print('irer: %d i: %d, pairs changed %d' % (iter, i, alphaPairsChanged))
        
        if alphaPairsChanged == 0:
            iter += 1
        else:
            iter = 0
        # print('iteration number: %d' % iter)
    
    return b, alphas

class OpStruct:
    def __init__(self, dataMatIn, classLabels, C, toler):
        self.X = dataMatIn
        self.labelMatrix = classLabels
        self.C = C
        self.tol = toler
        self.m = np.shape(dataMatIn)[0]
        self.alphas = np.mat(np.zeros((self.m, 1)))
        self.b = 0.0
        self.eCache = np.mat(np.zeros((self.m, 2)))

def calcEk(oS, k):
    fXk = float(np.multiply(oS.alphas, oS.labelMatrix).T * (oS.X * oS.X[k, :].T)) + oS.b
    Ek = fXk - float(oS.labelMatrix[k])

    return Ek

def selectJ(i, oS, Ei):
    maxK = -1
    maxDeltaE = 0
    Ej = 0
    oS.eCache[i] = [1, Ei]
    validEcacheList = np.nonzero(oS.eCache[: , 0].A)[0]
    if len(validEcacheList) > 1:
        for k in validEcacheList:
            if k == i:
                continue
            Ek = calcEk(oS, k)
            deltaE = np.abs(Ei - Ek)
            if deltaE > maxDeltaE:
                maxK = k
                maxDeltaE = deltaE
                Ej = Ek
        
        return maxK, Ej
    else:
        j = selectJrand(i, oS.m)
        Ej = calcEk(oS, j)
    
    return j, Ej

def updateEk(oS, k):
    Ek = calcEk(oS, k)
    oS.eCache[k] = [1, Ek]

def innerL(i, oS):
    Ei = calcEk(oS, i)
    if ((oS.labelMatrix[i] * Ei < -oS.tol) and (oS.alphas[i] < oS.C)) or ((oS.labelMatrix[i] * Ei > oS.tol) and (oS.alphas[i] > 0)):
        j, Ej = selectJ(i, oS, Ei)
        alphaIOld = oS.alphas[i].copy()
        alphaJOld = oS.alphas[j].copy()

        if oS.labelMatrix[i] != oS.labelMatrix[j]:
            L = max(0, oS.alphas[j] - oS.alphas[i])
            H = min(oS.C, oS.C + oS.alphas[j] - oS.alphas[i])
        else:
            L = max(0, oS.alphas[j] + oS.alphas[i] - oS.C)
            H = min(oS.C, oS.alphas[j] + oS.alphas[i])
        
        if L == H:
            # print('L == H')
            return 0
        
        eta = 2.0 * oS.X[i, :] * oS.X[j, :].T - oS.X[i, :] * oS.X[i, :].T - oS.X[j, :] * oS.X[j, :].T
        if eta >= 0:
            # print('eta >= 0')
            return 0
        
        oS.alphas[j] -= oS.labelMatrix[j] * (Ei - Ej) / eta
        oS.alphas[j] = clipAlpha(oS.alphas[j], H, L)
        updateEk(oS, j)
        if np.abs(oS.alphas[j] - alphaJOld) < 0.00001:
            # print('j not moving enough')
            return 0

        oS.alphas[i] += oS.labelMatrix[j] * oS.labelMatrix[i] * (alphaJOld - oS.alphas[j])
        updateEk(oS, i)

        b1 = oS.b - Ei - oS.labelMatrix[i] * (oS.alphas[i] - alphaIOld) * oS.X[i, :] * oS.X[i, :].T - oS.labelMatrix[j] * (oS.alphas[j] - alphaJOld) * oS.X[i, :] * oS.X[j, :].T
        b2 = oS.b - Ej - oS.labelMatrix[i] * (oS.alphas[i] - alphaIOld) * oS.X[i, :] * oS.X[j, :].T - oS.labelMatrix[j] * (oS.alphas[j] - alphaJOld) * oS.X[j, :] * oS.X[j, :].T 

        if (0 < oS.alphas[i]) and (oS.C > oS.alphas[i]):
            oS.b = b1
        elif (0 < oS.alphas[j]) and (oS.C > oS.alphas[j]):
            oS.b = b2
        else:
            oS.b = (b1 + b2) / 2.0

        return 1
    else:
        return 0

def smoP(dataMatIn, classLabels, C, toler, maxIter, kTup = ('lin', 0)):
    oS = OpStruct(np.mat(dataMatIn), np.mat(classLabels).transpose(), C, toler)
    iter = 0
    entireSet = True
    alphaPairsChanged = 0
    while (iter < maxIter) and ((alphaPairsChanged > 0) or (entireSet)):
        alphaPairsChanged = 0
        if entireSet:
            for i in range(oS.m):
                alphaPairsChanged += innerL(i, oS)
                # print('fullSet, iter: %d, i: %d, pairs changed %d' % (iter, i, alphaPairsChanged))
            iter += 1
        else:
            nonBoundIs = np.nonzero((oS.alphas.A > 0) * (oS.alphas.A < C))[0]
            for i in nonBoundIs:
                alphaPairsChanged += innerL(i, oS)
                # print('non-bound, iter: %d i: %d, pairs changed %d' % (iter, i, alphaPairsChanged))
            
            iter += 1
        
        if entireSet: 
            entireSet = False
        elif alphaPairsChanged == 0:
            entireSet = True
        # print('iteration number: %d' % iter)
    
    return oS.b, oS.alphas

def calcWs(alphas, dataArr, classLabels):
    X = np.mat(dataArr)
    labelMatrix = np.mat(classLabels).transpose()
    m, n = np.shape(X)
    w = np.zeros((n, 1))
    for i in range(m):
        w += np.multiply(alphas[i] * labelMatrix[i], X[i, :].T)
    
    return w

def testSmoP(dataArr, labelArr, alphas, b, ws):
    dataMatrix = np.mat(dataArr)
    m, n = np.shape(dataMatrix)
    ws = np.mat(ws)
    errorCount = 0.0
    for i in range(m):
        result = dataMatrix[i] * ws + b
        if result > 0:
            result = 1.0
        else:
            result = -1.0
        
        if result != labelArr[i]:
            errorCount += 1.0
    
    print('The error rate is %f' % (errorCount / float(m)))

# test
if __name__ == '__main__':
    dataArr, labelArr = loadDataSet('testSet.txt')
    b, alphas = smoP(dataArr, labelArr, 0.6, 0.001, 40)

    ws = calcWs(alphas, dataArr, labelArr)
    testSmoP(dataArr, labelArr, alphas, b, ws)
