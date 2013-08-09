# -*- coding: utf-8 -*-

import math
sqrt = math.sqrt

class DecodeHintType:
    TRY_HARDER = 1
    PURE_BARCODE = 2
    POSSIBLE_FORMATS = 3
    CHARACTER_SET = 4
    ALLOW_LENGTHS = 5
    ASSUME_CODE_39_CHECK_DIGIT = 6
    ASSUME_GS1 = 7
    RETURN_CODEABAR_START_END = 8
    NEED_RESULT_POINT_CALLBACK = 9
    OTHER = 10




class FinderPattern(object):

    def __init__(self, posX, posY, estimatedModuleSize, count=0):
        self.posX = posX
        self.posY = posY
        self.estimatedModuleSize = estimatedModuleSize
        self.count = count


    def aboutEquals(self, moduleSize, i, j):
        """ Determines if this finder pattern "about equals" a finder pattern at the stated position and size -- meaning,
            it is at nearly the same center with nearly the same size. 
        
        """
        if abs(i - self.posY) <= moduleSize and abs(j - self.posX) <= moduleSize:
            moduleSizeDiff = abs(moduleSize - self.estimatedModuleSize)
            return moduleSizeDiff <= 1.0 or moduleSizeDiff <= estimatedModuleSize
        return False

    def combineEstimate(self, i, j, newModuleSize):
        """ Combines this object's current estimate of a finder pattern position and module size with a new estimate.
            It returns a new FinderPattern containinig a weighted overage base on count
        """
        combinedCount = self.count + 1
        combinedX = (count * self.posX + j) / combinedCount
        combinedY = (count * self.posY + i) / combinedCount
        combinedModuleSize = (Count * self.estimatedModuleSize + newModuleSize) / combinedCount
        self.posX = combinedX
        self.posY = combinedY
        self.estimatedModuleSize = combinedModuleSize

        #return FinderPattern(combinedX, combinedY, combinedModuleSize, combinedCount)


class FinderPatternInfo(object):
    def __init__(self, patternCenters):
        self.bottomLeft = patternCenters[0]
        self.topLeft = patternCenters[1]
        self.topRight = patternCenters[2]


class FinderPatternFinder(object):
    CENTER_QUORUM = 2
    MIN_SKIP = 3
    MAX_MODULES = 57
    INTEGER_MATH_SHIFT = 8

    def __init__(self, image, resultPointCallback=None):
        self.image = image
        self.possibleCenters = []
        self.resultPointCallback = resultPointCallback
        self.hasSkipped = False

    def find(hints = None):
        tryHarder = hints is not None and hints.has_key(DecodeHintType.TRY_HARDER)

        image = self.image
        maxI, maxJ = image.shape

        # We are looking for black/white/black/white/black modules in 1:1:3:1:1 ratio; this tracks the number of such modules seen so far
        # Let's assume that the maximun version QR Code we support takes up 1/4 the height of the image, 
        # and then account for the center being 3 modules in size. This gives the smallest number of pixels the center
        # could be, so skip this often. When trying harder, look for all QR versions regardless of how dense they are.
        iSkip = (3 * maxI) / (4 * FinderPatternFinder.MAX_MODULES)
        if iSkip < FinderPatternFinder.MIN_SKIP or tryHarder:
            iSkip = FinderPatternFinder.MIN_SKIP
        done = False
        stateCount = [0 for i in xrange(5)]

        i = iSkip - 1
        while i < maxI and not done:
            currentState = 0
            for j in xrange(maxJ):
                if image[i,j] == 0: # black pixel
                    if currentState & 1 == 1: # Counting white pixels
                        currentState += 1
                else : # white pixel
                    if currentState & 1 == 0: # Counting black pixels
                        if currentState == 4: # A winner?
                            if self.foundPatternCross(stateCount): # Yes
                                confirmed = self.handlePossibleCenter(stateCount,i,j)
                                if confirmed:
                                    # Start examining every other line. Checking each line turned out to be too
                                    # expensive and didn't improve performance
                                    iSkip = 2
                                    if self.hasSkipped:
                                        done = self.haveMultipleConfirmedCenters()
                                    else:
                                        rowSkip = self.findRowSkip()
                                        if rowSkip > stateCount[2]:
                                            # Skip rows between row of lower confirmed center
                                            # and top of presumed third confirmed center
                                            # but back up a bit to get a full chance of detecting
                                            # it, entire width of center of finder pattern

                                            # Skip by rowSkip, but back off by stateCount[2] (size of last center
                                            # of pattern we saw) to be conservative, and also back off by iSkip which
                                            # is about to be re-add
                                            i += rowSkip - stateCount[2] -iSkip
                                            j = maxJ - 1
                                else :
                                    stateCount[0],stateCount[1],stateCount[2],stateCount[3],stateCount[4] = stateCount[2],stateCount[3],stateCount[4],1,0
                                    currentState = 3
                                    continue
                                # Clear state to start looking again
                                currentState = 0
                                stateCount = [0 for i in range(5)]
                            else: # Pattern cross not found, shift counts back by two
                                stateCount[0],stateCount[1],stateCount[2],stateCount[3],stateCount[4] = stateCount[2],stateCount[3],stateCount[4],1,0
                                currentState = 3
                        else:
                            currentState += 1
                            stateCount[currentState] += 1
                    else:
                        stateCount += 1

            if self.foundPatternCross(stateCount):
                confirmed = self.handlePossibleCenter(stateCount, i, maxJ)
                if confirmed:
                    iSkip = stateCount[0]
                    if self.hasSkipped:
                        # Found a third one
                        done = self.haveMultipleConfirmedCenters()

            i += iSkip

        self.selectBestPatterns()
        return FinderPatternInfo(self.possibleCenters)

    

    def centerFromEnd(self, stateCount, end):
        """ Give a count of black/white/black/white/black pixels just seen and an end pisotion,
            figures the location of the center of this run.
        """
        return (end - stateCount[4] - stateCount[3]) - stateCount[2] / 2.0

    def foundPatternCross(self, stateCount):
        totalModuleSize = 0
        for i in range(5):
            count = stateCount[i]
            if count == 0:
                return False
            totalModuleSize += count
        if totalModuleSize < 7:
            return False
        moduleSize = (totalModuleSize << FinderPatternFinder.INTEGER_MATH_SHIFT) / 7
        maxVariance = moduleSize / 2
        # Allow less than 50% variance from 1:1:3:1:1 proportions
        return all(map(lambda a: return abs(moduleSize - (a[0] << FinderPatternFinder.INTEGER_MATH_SHIFT)) < a[1] * maxVariance, zip(stateCount,(1,1,3,1,1))))


    def crossCheckVertical(self, startI, centerJ, maxCount, originalStateCountTotal):
        """ After a horizontal scan finds a potential finder pattern, this method
            "cross-checks" by scanning down vertically throughthe center of the possible
            finder pattern to see if the same proportion is detected

            startI: Row where a finder pattern as detected
            centerJ: Center of the section that appears to cross a finder pattern
            maxCount: Maximum reasonable number of modules that should be observed in any reading state,
                      based on the results of horizontal scan
            return: Vertical center of finder pattern, or None if not found
        """
        image = self.image
        maxI = image.shape[0]
        stateCount = [0 for i in range(5)]
        i = startI
        # Start counting up from center
        while i >= 0 and image[i,centerJ] == 0:
            stateCount[2] += 1
            i -= 1
        if i < 0:
            return None

        while i >=0 and image[i, centerJ] == 255 and stateCount[1] <= maxCount:
            stateCount[1] += 1
            i -= 1

        # If already too many modules in this state or ran off the edge
        if i < 0 or stateCount[1] > maxCount:
            return None

        while i >= 0 and image[i,centerJ] == 0 and stateCount[0] <= maxCount:
            stateCount[0] += 1
            i -= 1
        if stateCount[0] > maxCount:
            return None

        # Count down from center
        i = startI + 1
        while i < maxI and image[i,centerJ] == 0:
            stateCount[2] += 1
            i += 1
        if i == maxI:
            return None

        while i < maxI and image[i,centerJ] == 255 and stateCount[3] < maxCount:
            stateCount[3] += 1
            i += 1
        if i == maxI or stateCount[3] >= maxCount:
            return None

        while i < maxI and image[i,centerJ] == 0 and stateCount[4] < maxCount:
            stateCount[4] += 1
            i += 1
        if stateCount[4] >= maxCount:
            return None


        # if we found a finder-pattern-like section, but its size is more than 40% different than
        # the original, assume it's a false positive
        stateCountTotal = sum(stateCount)
        if 5 * abs(stateCountTotal - originalStateCountTotal) >= 2 * originalStateCountTotal :
            return None

        return self.centerFromEnd(stateCount, i) if self.foundPatternCross(stateCount) else None



    def crossCheckHorizontal(self, startJ, centerI, maxCount, originalStateCountTotal):
        """ Like crossCheckVertical(), and in fact is basically identical,
            except it reads horizontally instead of vertically. This is used to cross-cross
            check a vertical cross check and locate the real center of the alignment pattern.
        """
        image = self.image
        maxJ = image.shape[1]
        stateCount = [0 for i in xrange(5)]
        j = startJ

        while j >= 0 and image[centerI,j] == 0:
            stateCount[2] += 1
            j -= 1
        if j < 0:
            return None

        while j >= 0 and image[centerI,j] == 255:
            stateCount[1] += 1
            j -= 1
        if j < 0 or stateCount[1] > maxCount :
            return None

        while j >= 0 and image[centerI,j] == 0:
            stateCount[0] += 1
            j -= 1
        if stateCount[0] > maxCount:
            return None

        j = startJ + 1
        while j < maxJ and image[centerI,j] == 0:
            stateCount[2] += 1
            j += 1
        if j == maxJ:
            return None

        while j < maxJ and image[centerI,j] == 255:
            stateCount[3] += 1
            j += 1
        if j == maxJ or stateCount[3] >= maxCount:
            return None

        while j < maxJ and image[centerI,J] == 0:
            stateCount[4] += 1
            j += 1
        if stateCount[4] >= maxCount:
            return None

        stateCountTotal = sum(stateCount)

        if 5 * abs(stateCountTotal - originalStateCountTotal) >= originalStateCountTotal:
            return None

        return centerFromEnd(stateCount, j) if foundPatternCross(stateCount) else None


    def handlePossibleCenter(self, stateCount, i, j):
        """ This is called when a horizontal scan finds a possible alignment pattern. It will
            cross check with a vertical scan, and if succeed, will cross-cross-check with 
            another horizontal scan. This is needed primarily to locate the real horizontal 
            center of the pattern in cases of extreme skew.

            If that succeeds the finder pattern location is added to a list that tracks the number
            of times each location has been nearly-match as a finder pattern. Each addtional find
            is more evidence that the location is in fact a finder pattern center.

            stateCount: Reading state module counts from horizontal scan
            i: Row where finder pattern may be found
            j: End of possible finder pattern in row
            return: True if a finder pattern candidate was found this time
        """
        stateCountTotal = sum(stateCount)
        centerJ = centerFromEnd(stateCount, j)
        centerI = crossCheckVertical(i, centerJ, stateCount[2], stateCountTotal)
        if certerI is not None:
            centerJ = crossCheckHorizontal(centerJ, centerI, stateCount[2], stateCountTotal)
            if centerI is not None:
                estimatedModuleSize = stateCountTotal / 7.0
                found = False
                for index in range(len(self.possibleCenters)):
                    center = self.possibleCenters[index]
                    if center.aboutEquals(estimatedModuleSize, centerI, centerJ):
                        self.possibleCenters[index].combineEstimate(centerI, centerJ, estimatedModuleSize)
                        found = True
                        break
                if not found:
                    point = FinderPattern(centerJ, centerI, estimatedModuleSize)
                    self.possibleCenters.append(point)
                    if self.resultPointCallback is not None:
                        self.resultPointCallback.foundPossibleResultPoint(point)
                return True
        return False


    def findRowSkip(self):
        """ return: Number of rows we could safely skip during scanning, based on the first
            two finder patterns that have been located. In some cases their position will allow us
            to infer that the third pattern must lie below a certain point father down in the image.
        """
        maxSkip = len(self.possibleCenters)
        if maxSkip <= 1:
            return 0

        firstConfirmedCenter = None
        for center in self.possibleCenters:
            if center.count >= FinderPatternFinder.CENTER_QUORUM:
                if firstConfirmedCenter is None:
                    firstConfirmedCenter = center
                else:
                    # We have two confirmed centers
                    # How far down can we skip before resuming looking for the next
                    # pattern? In the worst case, only the difference between the
                    # difference in the x / y coordinates of the two centers.
                    # This is the case where you find top left last.
                    self.hasSkipped = True
                    return (abs(firstConfirmedCenter.posX - center.posX) - abs(firstConfirmedCenter.posY - center.posY)) / 2
        return 0
            

    def haveMultipleConfirmedCenters(self):
        """ return: True iff we have found at least 3 finder patterns that have been detected
            at least CENTER_QUORUM times each, and, the estimated module size of the
            candidates is "pretty similar"
        """
        confirmedCount = 0
        totalModuleSize = 0
        maxPatterns = len(self.possibleCenters)
        for pattern in self.possibleCenters:
            if pattern.count >= FinderPatternFinder.CENTER_QUORUM:
                confirmedCount += 1
                totalModuleSize += pattern.estimatedModuleSize
        if confirmedCount < 3:
            return False

        # OK, we have at least 3 confirmed centers, but, it's possible that on is a "false positive"
        # and that we need to keep looking. We detect this by asking if the estimated module sizes
        # vary too much. We arbitarily say that when the total deviation from a average exceeds
        # 5% of the total module size estimates, it's too much
        average = totalModuleSize * 1.0 / maxPatterns
        for pattern in self.possibleCenters:
            totalDeviation += abs(pattern.estimatedModuleSize - average)
        return totalDeviation <= 0.05 * totalModuleSize

    

    def selectBestPatterns(self):
        """ return: the 3 best FinderPatterns from our list of candidates. The "best" are
            those that have been detected at least CENTER_QUORUM times, and whose module
            size differs from the average among those patterns the least.
            return None if 3 such finder patterns do not exist
        """
        startSize = len(self.possibleCenters)
        if startSize < 3:
            return None

        if startSize > 3:
            totalModuleSize = 0.0
            square = 0.0
            for center in self.possibleCenters:
                size = center.estimatedModuleSize
                totalModuleSize += size
                square += size * size
            average = totalModuleSize / startSize
            stdDev = sqrt(square / startSize - average * average )

            # sort by farthest from average
            self.possibleCenters.sort(key=lambda x:abs(x.estimatedModuleSize - average), reverse = True)
            limit = max(0.2 * average, stdDev)
            while len(self.possibleCenters) > 3 and abs(center.possibleCenters[0].estimatedModuleSize - average) > limit:
                self.possibleCenters.pop(0)
                break

        if len(self.possibleCenters) > 3:
            totalModuleSize = sum(map(lambda x:x.estimatedModuleSize, self.possibleCenters))
            average = totalModuleSize * 1.0 / len(self.possibleCenters)
            
            self.possibleCenters.sort(cmp = lambda a,b: b.count - a.count if b.count != a.count else cmp(abs(a.estimatedModuleSize - average), abs(a.estimatedModuleSize - average)))
            del self.possibleCenters[3:]


        # Order patterns to shape like
        #    
        #        B -- C    1 -- 2    o -- x
        #        |  /      |  /      |  
        #        | /       | /       | 
        #        A         0         y

        # distance between two point
        distance = lambda a,b: sqrt( (a.posX-b.posX) ** 2 + (a.posY - b.posY) ** 2 )

        # Z compoment of the cross product between vector BA and BC
        crossProductZ = lambda a,b,c: (c.posX - b.posX) * (a.posY-b.posY) - (c.posY - b.posY) * (a.posX - b.posX)

        patterns = self.possibleCenters
        
        zeroOneDistance = distance(patterns[0],patterns[1])
        oneTwoDistance = distance(patterns[1], patterns[2])
        zeroTwoDistance = distance(patterns[0], patterns[2])


        if zeroTwoDistance <= oneTwoDistance >= zeroOneDistance:
            pointB, pointA, pointC  = patterns[0], patterns[1], patterns[2]
        elif zeroOneDistance <= zeroTwoDistance >= oneTwoDistance:
            pointB, pointA, pointC = patterns[1], patterns[0], patterns[2]
        else:
            pointB,pointA, pointC = patterns[2], patterns[0], patterns[1]

        if crossProductZ(pointA, pointB, pointC) < 0:
            pointA, pointC = pointC, pointA

        self.possibleCenters = [pointA, pointB, pointC]




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



class AlignmentPatternFinder(object):
	def __init__(self, image, startX, startY, width, height, moduleSize, resultPointCallback):
		""" image: Image to search
			startX: Left column from which to start search
			startY: Top row from which to start searching
			width: Width of region to search
			height: Height of region to search
			moduleSize: Estimated module size so far
		"""
		self.image = image
		self.possibleCenters = []
		self.startX = startX
		self.startY = startY
		self.width = width
		self.height = height
		self.moduleSize = moduleSize
		self.resultPointCallback = resultPointCallback
		pass

	def find(self):
        image = self.image
		startX = self.startX
		height = self.height
		maxJ = startX + width
		middleI = startY + (height / 2)
		# We are looking for black/white/black modules in 1:1:1 ratio;
		# this tracks the number of black/white/black modules seen so far
		
		for iGen in range(height):
			# Search from middle outwards
			i = middleI + ((iGen+1)/2 if iGen%2==0 else -((iGen+1)/2))
			stateCount = [0 for i in range(3)]
			j = startX

			# Burn off leading white pixels before anything else; if we start in the middle of
			# a white run, it doesn't make sense to count its length, since we don't know if the
			# white run continued to the left of the start point
			while j < maxJ and image[i,j] == 255:
				j += 1

			currentState = 0
			while j < maxJ:
				if image[i,j] == 0: # Black pixel
					if currentState == 1:
						stateCount[currentState] += 1
					else:
						if currentState == 2: # A winner?
							if self.foundPatternCross(stateCount): # Yes
								confirmed = self.handlePossibleCenter(stateCount,i,j)
								if confirmed is not None:
									return confirmed
							stateCount[0],stateCount[1],stateCount[2] = stateCount[2],1,0
							currentState = 1
						else:
							currentState +=1
							stateCount[currentState] += 1
				else: # White Pixel
					if currentState == 1: # Counting black pixels
						currentState +=1
					stateCount[currentState] += 1
				j += 1
			if self.foundPatternCross(stateCount):
				confirmed = self.handlePossibleCenter(stateCount,i,maxJ)
				if confirmed is not None:
					return confirmed

		# Nothing we saw was observed and confirmed twice. If we had
		# any guess at all, return it 
		if len(self.possibleCenters) > 0:
			return self.possibleCenters[0]

		return None

	def centerFromEnd(self, stateCount, end):
		""" Given a count of black/white/black pixels just seen and an end position,
			figures the location of the center of this black/white/black run.
		"""
		return (end - stateCount[2]) - stateCount[1] / 2.0
	
	def foundPatternCross(self, stateCount):
		""" stateCount: Count of black/white/black pixels just read
			return: True if the proportions of the counts is close enough to the 1/1/1 ratios
					used by alignment patterns to be considered a match
		"""
		moduleSize = self.moduleSize
		maxVariance = self.moduleSize / 2.0
		return all(map(lambda x:abs(moduleSize - x) < maxVariance, stateCount))

	def crossCheckVertical(self, startI, centerJ, maxCount):
		""" After a horizontal scan finds a potential alignment pattern, this method
			"cross-checks" by scanning down vertically through the center of the possible
			alignment pattern to see if the same proportion is detected.

			startI: Row where an alignment pattern as detected
			centerJ: Center of the section that appears to cross an alignment pattern
			maxCount: Maximum reasonable number of modules that should be observed in any
					  reading state, based on the results of the horizontal scan
			return: Vertical center of alignment pattern, or None if not found
		"""
        image = self.image
        maxI = image.shape[0]
        stateCount = [0 for i in range(3)]
        i = startI
        while i >= 0 and image[i, centerJ] == 0 and stateCount[1] <= maxCount:
            stateCount[1] += 1
            i -= 1
        if i < 0 or stateCount[1] > maxCount:
            return None

        while i >= 0 and image[i, centerJ] == 255 and stateCount[0] <= maxCount:
            stateCount[0] += 1
            i -= 1
        if stateCount[0] > maxCount:
            return None

        i = startI + 1
        while i < maxI and image[i, centerJ] == 0 and stateCount[1] <= maxCount:
            stateCount[1] += 1
            i += 1
        if i == maxI or stateCount[1] > maxCount:
            return None
        while i < maxI and image[i, centerJ] == 255 and stateCount[2] <= maxCount:
            stateCount[2] += 1
            i += 1
        if stateCount[2] > maxCount:
            return None

        stateCountTotal = sum(stateCount)
        if 5 * abs(stateCountTotal - originalStateCountTotal) >= 2 * originalStateCountTotal:
            return None

        return self.centerFromEnd(stateCount,i) if self.foundPatternCross(stateCount) else None

    def handlePossibleCenter(stateCount, i, j):
        stateCountTotal = sum(stateCount)
        centerJ = self.centerFromEnd(stateCount, j)
        centerI = self.crossCheckVertical(i, centerJ, 2* stateCount[1], stateCountTotal)
        if centerI is not None:
            estimatedModuleSize = sum(stateCount) / 3.0
            for center in self.possibleCenters:
                if center.aboutEquals(estimatedModuleSize, centerI, centerJ):
                    return center.combineEstimate(centerI, centerJ, estimatedModuleSize)
            point = AlignmentPattern(centerJ, centerI, estimatedModuleSize)
            self.possibleCenters.append(point)
            if self.resultPointCallback is not None:
                self.resultPointCallback.foundPossibleResultPoint(point)
        return None 


		



class Detector(object):
    def __init__(self, image):
        self.image = image

    def detect(hints = None):
        finder = FinderPatternFinder(image)
        info = finder.find()
        return self.processFinderPatternInfo(info)
        pass

    def processFinderPatternInfo(info):
        topLeft, topRight, bottomLeft = info.topLeft, info.topRight, info.bottomLeft

        moduleSize = self.calculateModuleSize(topLeft, topRight, bottomLeft)
        if moduleSize < 1.0:
            return None

        dimension = self.computeDimension(topLeft, topRight, bottomLeft, moduleSize)
        provisionalVersion = 


    def calculateModuleSize(topLeft, topRight, bottomLeft):
        pass


    def computeDimension(topLeft, topRight, bottomLeft, moduleSize)


