# -*- coding: utf-8 -*-


class FinderPattern(object):

    def __init__(self, posX, posY, estimatedModuleSize, count=0):
        self.posX = posX
        self.posY = posY
        self.estimatedModuleSize = estimatedModuleSize
        self.count = count


    def aboutEquals(self, moduleSize, i, j):
        """Determines if this finder pattern "about equals" a finder pattern at the stated position and size -- meaning,
           it is at nearly the same center with nearly the same size. 
        
        """
        if abs(i - self.posY) <= moduleSize and abs(j - self.posX) <= moduleSize:
            moduleSizeDiff = abs(moduleSize - self.estimatedModuleSize)
            return moduleSizeDiff <= 1.0 or moduleSizeDiff <= estimatedModuleSize
        return False

    def combineEstimate(self, i, j, newModuleSize):
        """Combines this object's current estimate of a finder pattern position and module size with a new estimate.
           It returns a new FinderPattern containinig a weighted overage base on count
        """
        combinedCount = self.count + 1
        combinedX = (count * self.posX + j) / combinedCount
        combinedY = (count * self.posY + i) / combinedCount
        combinedModuleSize = (Count * self.estimatedModuleSize + newModuleSize) / combinedCount
        return FinderPattern(combinedX, combinedY, self.estimatedModuleSize, combinedCount)





class FinderPatternFinder(object):

    def __init__(self, image, resultPointCallback):
        self.image = image
        self.possibleCenters = []
        self.crossCheckStateCount = []
        self.resultPointCallback = resultPointCallback

    def find(hints = None):
        tryHarder = hints is not None and hints.hasKey("")
        pass

class AlignmentPattern(object):

    def __init__(self, posX, posY, estimatedModuleSize):
        self.posX = posX
        self.posY = posY
        self.estimatedModuleSize = estimatedModuleSize

    def aboutEquals(self, moduleSize, i, j):
        if abs(i - self.posY) <= moduleSize and abs(j - self.posX) <= moduleSize:
            moduleSizeDiff = abs(moduleSize - self.estimatedModuleSize)
            return moduleSizeDiff <= 1.0 or moduleSizeDiff <= estimatedModuleSize
        return False

    def combineEstimate(self, i, j, newModuleSize):
        combinedX = (self.posX + j) / 2.0
        combinedY = (self.posY + i) / 2.0
        combinedModuleSize = (self.estimatedModuleSize + newModuleSize) / 2.0
        return AlignmentPattern(combinedX, combinedY, combinedModuleSize)

