import sys


# ISO 18004:2006


class Version(object):

    VERSION_DECODE_INFO = [0x07C94, 0x085BC, 0x09A99, 0x0A4D3, 0x0BBF6,
      0x0C762, 0x0D847, 0x0E60D, 0x0F928, 0x10B78,
      0x1145D, 0x12A17, 0x13532, 0x149A6, 0x15683,
      0x168C9, 0x177EC, 0x18EC4, 0x191E1, 0x1AFAB,
      0x1B08E, 0x1CC1A, 0x1D33F, 0x1ED75, 0x1F250,
      0x209D5, 0x216F0, 0x228BA, 0x2379F, 0x24B0B,
      0x2542E, 0x26A64, 0x27541, 0x28C69]

    VERSIONS = buildVersions()

    def __init__(self, versionNumber, alignmentPatternCenters, ecBlocks):
        self.versionNumber = versionNumber
        self.alignmentPatternCenters = alignmentPatternCenters
        self.ecBlocks = ecBlocks
        total = 0
        ecCodewords = ecBlocks[0].getTotalECCodewords()
        ecbArray = ecBlocks[0].getECBlocks()
        for ecBlock in ecbArray:
            total += ecBlock.getCount() * (ecBlock.getDataCodewords() + ecCodewords)
        self.totalCodewords = total
        pass

    def getVersionNumber(self):
        return self.versionNumber

    def getAlignmentPatternCenters(self):
        return self.alignmentPatternCenters

    def getTotalCodewords(self):
        return self.totalCodewords

    def getDimensionForVersion(self):
        return 17 + 4 * self.versionNumber

    def getECBlocksForLevel(self, ecLevel):
        return self.ecBlocks[ecLevel.ordinal()]

    @staticmethod
    def getProvisionalVersionsForDimension(dimension):
        if dimension % 4 != 1:
            raise Exception("Format Error")
        try:
            return getVersionForNumber((dimension - 17) >> 2)
        except Exception,e:
            raise Exception("Format Error")

    @staticmethod
    def getVersionForNumber(versionNumber):
        if version < 1 or versionNumber > 40:
            raise Exception("Illegal argument")
        return Version.VERSIONS[versionNumber - 1]

    @staticmethod
    def decodeVersionInformation(versionBits):
        bestDifference = sys.maxint
        bestVersion = 0
        for i in range(len(Version.VERSION_DECODE_INFO)):
            targetVersion = Version.VERSION_DECODE_INFO[i]
            if targetVersion == versionBits:
                return Version.getVersionForNumber(i + 7)








# Encapsulates a set of error-correction blocks in one symbol version. Most versions will
# use blocks for differing sizes within one version, so, this encapsulates the parameters for
# each set of blocks. It also holds the number of error-correction codewords per block since it
# will be the same across all blocks within one version.

class ECBlocks(object):

    def __init__(self, ecCodewordsPerBlock, ecBlocks):
        self.ecCodewordsPerBlock = ecCodewordsPerBlock
        self.ecBlocks = ecBlocks

    def getNumBlocks(self):
        total = 0
        for ecBlock in self.ecBlocks:
            total += ecBlock.count
        return total

    def getTotalECCodewords(self):
        return self.ecCodewordsPerBlock * self.getNumBlocks()

    def getECBlocks(self):
        return self.ecBlocks



# Encapsulates the parameters for one error-correction block in one symbol version.
# This includes the number of data codewords, and the number of times a block with these
# parameters is used consecutively in the QR code version's format.

class ECB(object):
    def __init__(self, count, dataCodewords):
        self.count = count
        self.dataCodewords = dataCodewords
