#!/usr/bin/env python
    
###Imports and Variable Initalizations###
import re, copy, os, sys, subprocess
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Alphabet import IUPAC
from Bio import SeqIO
from subprocess import *
from readtools_exceptions import *

program_name = 'readtools.py'
program_version = '1.0.0'
phredConversion = {'sanger':'''!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHI''', \
                   'solexa':';<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh', \
                   'illumina':'@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefgh',\
                   'all' : '''!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~'''}
progName, progVersion = ('readtools.py','1.0.0')

cigarInsertTypes = {'D':'*', 'P':'_', 'N':'~'} #cigar types that are used as spacers in alignments and are not represented by a corresponding index in the unaligned sequence
cigarExtraTypes = ('I', 'P')
cigarAlignedTypes = ('M', 'I', '=', 'X') #cigar types that are present in an alignment and are represented by a corresponding index in the unaligned sequence 
cigarIgnoredTypes = ('S',) #cigar types that are not present in an alignment, but are in the unaligned sequence
cigarAbsentTypes = ('H',) #cigar types that are not present in an alignment or the unaligned sequence

cigarTypes = tuple(cigarInsertTypes.keys()) + cigarAlignedTypes + cigarIgnoredTypes + cigarAbsentTypes
cigarPresentTypes = tuple(cigarInsertTypes.keys()) + cigarAlignedTypes
gapPlaceholder = cigarInsertTypes['N']


###Global Functions###
def iterateGenerators(generators):
    '''Version 1.0
    Takes a list of generators, iterates all of them once, and return the result in a list. Terminated generators are removed from the input list.'''
    output, closedGenerators = [], []
    for genIndex in range(0,len(generators)): #for every read that is currently being read through
        try: output.append(generators[genIndex].next())
        except StopIteration: closedGenerators.append(genIndex)
    closedGenerators.reverse()
    for index in closedGenerators: del generators[index] #removes read interator objects that have ended
    else: return zip(*output)

def withinRange(number, aRange):
    if aRange[0] != None and number < aRange[0]: return False
    if aRange[1] != None and number > aRange[1]: return False
    else: return True

def withinRanges(value, ranges):
    for aRange in ranges:
        if withinRange(value, aRange): return True
    return False

def getVariantFrequency(sequences):
    '''Version 1.0
    Takes a list of strings and counts the number of repetative strings. Returns a list of tuples in the format [(count, variant), ...]
    and sorts them based on frequency.'''
    encounteredSequences, sequenceCount = [], []
    for sequence in sequences:
        if sequence in encounteredSequences:
            sequenceCount[encounteredSequences.index(sequence)] += 1 #if sequence has already been found
        else:
            encounteredSequences.append(sequence)
            sequenceCount.append(1)
    output = zip(sequenceCount, encounteredSequences)
    output.sort()
    output.reverse()
    return output

def getMajority(bases):
    baseFrequencies = getVariantFrequency(bases) 
    if len(baseFrequencies) == 0:
        return gapPlaceholder
    else:
        return baseFrequencies[0][1]

def getIUPAC(baseValues, deletionCharacter = '*', paddingCharacter = '_', skippedCharacter = '~'):
    def removeRepeats(aList):
        for entry in aList:
            if aList.count(entry) > 1:
                aList.remove(entry)
                return removeRepeats(aList)
        return aList
    def IUPAC(bases):
        conversion = {'CT':'Y','AG':'R','AT':'W','CG':'S','GT':'K','AC':'M','AGT':'D','ACG':'V','ACT':'H','CGT':'B','ACGT':'N'}
        bases.sort()  #['A', 'C', 'G', 'T']
        if bases[0].islower():
            bases = map(str.upper,bases)
            return str.lower(conversion[''.join(bases)])
        else:
            return conversion[''.join(bases)]
    chars = removeRepeats(list(baseValues))
    chars.sort()  #['-', 'A', 'C', 'G', 'N', 'T', 'a', 'c', 'g', 'n', 't', '~']
    if len(chars) == 0: return gapPlaceholder
    if len(chars) == 1: return chars[0]
    #if chars[-1] == '~':   #converts '~' to '-'
    #    del chars[-1]
    #    if chars[0] != '-': chars.insert(0,'-')
    priorityList = ('ACGT', 'N', deletionCharacter, 'acgt', 'n', paddingCharacter, skippedCharacter)
    for group in priorityList:
        matchs = [base for base in chars if group.find(base) != -1]
        if len(matchs) == 0: continue
        elif len(matchs) == 1: return matchs[0]
        else: return IUPAC(matchs)

def parseNucmer(filePath):
    '''Version 1.0'''
    fileHandle = open(filePath, 'r')
    fileData = fileHandle.read()
    fileHandle.close()
    nucInPaths = fileData[0]
    #a '>' appears before the name of every contig and each match is sepeated by a '0' on its own line (i.e. '\n0\n')
    #data is parsed by contig ('>'), match ('\n0\n'), and line '\n'. 
    contigData = [[cntg.split('\n') for cntg in group.split('\n0\n')[:-1]] for group in fileData[1:].split('>')][1:]
    if len(contigData) == 0: return None
    for cIndex in range(0,len(contigData)):
        if len(contigData[cIndex]) > 1:
            for gIndex in range(1,len(contigData[cIndex])):
                cntgHeadParts = contigData[cIndex][0][0].split()
                #cntgHeadParts[1] += '(%d)' % (gIndex + 1)
                contigData[cIndex][gIndex].insert(0,' '.join(cntgHeadParts))   #adds contigs information to each sub contig
    contigData = [cntg for group in contigData for cntg in group]   #makes into one contig list
    headers = zip(*[cntg[0].split(' ') for cntg in contigData])
    refHeads, cntgHeads, refLenghts, cntgLengths = (headers[0],list(headers[1]),map(int,headers[2]),map(int,headers[3]))
    alignStats = [map(int,cntg[1].split()) for cntg in contigData]
    deltas = [map(int,cntg[2:]) for cntg in contigData]
    outList = (cntgHeads, refHeads, refLenghts, cntgLengths, alignStats, deltas)
    return outList

def interpretFastaAlignment(query, reference, deletionCharacter = '*', paddingCharacter = '_', skippedCharacter = '~', lowerCaseIsUnaligned = True):
    query.padding = 0
    offset = re.match(paddingCharacter + '*', str(query.seq)).end()
    query.seq = query.seq[offset:]
    query.reference = reference
    patternToCigar = {deletionCharacter : 'D', skippedCharacter : 'N'}
    if paddingCharacter != deletionCharacter:
        patternToCigar[paddingCharacter] = 'P'
    comparisonToCigar = {'MM' : 'M', 'MI' : 'I', 'DM' : 'D', 'NM' : 'N', 'MP' : 'I', 'PM' : 'P', 'PP' : 'P', 'II' : 'I', 'IM' :'D', 'NP' : 'P', 'DP' : 'D'}
    if lowerCaseIsUnaligned:
        unalignedStartLength = re.match('[a-z]*', str(query.seq)).end()
        unalignedEndLength = re.match('[a-z]*', ''.join(list(reversed(list(query.seq))))).end()
        alignedLength = len(query.seq) - unalignedStartLength -unalignedEndLength
        query.start = unalignedStartLength + offset
        #query.end = len(query.seq) - query.seq.count(deletionCharacter) - re.match('[a-z]*', str(reversed(query.seq))).end()
        cigar = [[unalignedStartLength, 'S']]
    else:
        query.start = offset
        alignedLength = len(query.seq)
        #query.end = len(query.seq) - query.seq.count(deletionCharacter) - 1
        cigar = [['Temp', 'Temp']]
        
    print query.id, '%s...%s' % (str(reference.seq[query.start : query.start + alignedLength])[:10], str(reference.seq[query.start : query.start + alignedLength])[-10:])
    print unalignedStartLength, unalignedEndLength, query.start, alignedLength
    querySequence = query.seq[unalignedStartLength : unalignedStartLength + alignedLength]
    referenceSequence = reference.seq[query.start : query.start + alignedLength]
    for queryBase, referenceBase in zip(querySequence, referenceSequence):
        if re.match('[a-zA-Z]', queryBase):
            queryCigar = 'M'
        else:
            queryCigar = patternToCigar[queryBase]
        if re.match('[a-zA-Z]', referenceBase):
            referenceCigar = 'M'
        elif referenceBase == paddingCharacter:
            referenceCigar = 'P'
        baseCigar = comparisonToCigar[queryCigar + referenceCigar]
        if cigar[-1][1] == baseCigar:
            cigar[-1][0] += 1
        else:
            cigar.append([1, baseCigar])
    if lowerCaseIsUnaligned:
        cigar.append([unalignedEndLength, 'S'])
    else:
        del cigar[0]
    query.cigar = ''.join([str(part) for pair in cigar for part in pair])
    query.seq = str(query.seq).replace(deletionCharacter, '')
    query.seq = str(query.seq).replace(paddingCharacter, '')
    query.seq = str(query.seq).replace(skippedCharacter, '')
    query.end = query.start + query.alignedReferenceLength() - 1
    query.refreshAlignment()
    print query.id, query.cigar
    return query

###Sequence Object Classes###
class AttributeFilter(object):
    '''Version 1.0'''
    def __init__(self, function, acceptableRanges):
        self.function = function
        self.acceptableRanges = acceptableRanges
    def __call__(self, *arguments):
        value = self.function(*arguments)
        return withinRanges(value, self.acceptableRanges)

class CustomizedFunction(object):
    '''Version 1.0'''
    def __init__(self, function, **kwargs):
        self.function = function
        self.kwargs = kwargs
    def __call__(self, *arguments):
        return self.function(*arguments, **self.kwargs)

    
class Alignment(SeqRecord):
    '''Version 2.1'''
    def cigarIter(self):
        '''Returns the two parts of each pair the cigar sequence: (count, letter)'''
        for matchObj in re.finditer('([0-9]+)([a-zA-Z])', self.cigar):
            yield int(matchObj.group(1)), matchObj.group(2)
    def indexIter(self):
        '''Version 1.1
        Returns the unaligned sequence index for aligned portions of the sequence and the cigar character one base at a time.
        An index of 'None' indicates that the base is an inserted spacer (e.g. deletion). 
        Output: (unaligned_sequence_index, cigar_letter)'''
        baseIndex = 0
        for length, letter in self.cigarIter():
            if letter in cigarAlignedTypes:
                for count in range(0,length):
                    yield (baseIndex, letter)
                    baseIndex += 1
            elif letter in cigarInsertTypes:
                for count in range(0,length): yield (None, letter)
            elif letter in cigarIgnoredTypes: baseIndex += length
            else: assert letter in cigarTypes
    def selfIndexIter(self):
        for index, cigarType in Alignment.indexIter(self): yield (self, index, cigarType)
    def __init__(self, seq, start = None, reference = None, cigar = None, mate = None, mateStart = None, flag = None, quality = None, sortAttr = 'start', **kwargs):
        SeqRecord.__init__(self, seq, **kwargs)
        variables,  arguments = vars(), dir()
        arguments.remove('self')
        arguments.remove('kwargs')
        arguments.remove('seq')
        for keyword in arguments: setattr(self, keyword, variables[keyword]) #assignes a varible to this instance for each keyword argument; equivalent to self.x = x
        for key, value in kwargs.iteritems(): setattr(self, key, value)
    @classmethod
    def fromRecord(cls, record, **kwargs):
        '''Alternate constructor function that makes an instance of alignment using the information from a seq Record object. '''
        instance = Alignment(record.seq, **kwargs)
        for key, value in record.__dict__.iteritems(): instance.__dict__[key] = value #Overrides keyword arguments that are the same as record data.
        if instance.cigar == None:
            instance.cigar = str(len(instance.seq)) + 'M'
        return instance
    def _compare(self, other, func):
        try:
            attributeA = getattr(self, self.sortAttr)
            if hasattr(attributeA, '__call__'): attributeA = attributeA()
            attributeB = getattr(other, other.sortAttr)
            if hasattr(attributeB, '__call__'): attributeB = attributeB()
            return func(attributeA, attributeB)
        except: return NotImplemented
    def __lt__(self, other): return self._compare(other, lambda a, b: a < b)
    def __le__(self, other): return self._compare(other, lambda a, b: a <= b)
    def __eq__(self, other): return self._compare(other, lambda a, b: a == b)
    def __ne__(self, other): return self._compare(other, lambda a, b: a != b)
    def __gt__(self, other): return self._compare(other, lambda a, b: a > b)
    def __ge__(self, other): return self._compare(other, lambda a, b: a >= b)
    def __len__(self):
        '''Version 1.1
        Returns the length of the sequence as determined by the cigar sequence. Faster than len(alignment.alignedSeq())'''
        return sum([length for length, letter in self.cigarIter() if letter in cigarPresentTypes and letter != 'P'])
    def __iter__(self):
        '''Version 1.0
        Returns the aligned portions of the sequence one base at a time.'''
        for index, cigarLetter in self.indexIter():
            if index is None:
                yield insertTypes[cigarLetter]
            else:
                yield self.seq[index]           
    def alignedSeq(self):
        '''Returns the aligned portions of the sequence.'''
        return list(self.__iter__())
    def alignedLength(self):
        '''Version 1.1
        Returns the length of the sequence when aligned as determined by the cigar sequence. Faster than len(alignment.alignedSeq())'''
        return sum([length for length, letter in self.cigarIter() if letter in cigarPresentTypes and letter != 'P' and letter != 'S'])
    def alignedReferenceLength(self):
        '''Version 1.1
        Returns the length of reference that the sequence as determined by the cigar sequence.'''
        return sum([length for length, letter in self.cigarIter() if letter in cigarPresentTypes and letter not in ['S', 'I']])
    def insertionCount(self):
        return sum([length for length, letter in self.cigarIter() if letter in cigarExtraTypes])
    def end(self):
        return self.start + self.__len__() - 1 - self.insertionCount()
    def hasIndex(self, index):
        return self.start <= index and self.end() >= index
    def baseCounts(self, caseSensitive = True):
        output = []
        for count, base in getVariantFrequency(self.seq):
            output.append([base, count])
        return output
    def baseRatios(self, caseSensitive = True):
        bases, counts = zip(*self.baseCounts(caseSensitive = caseSensitive))
        totalCount = sum(counts)
        output = []
        for base, count in zip(bases, counts):
            ratio = float(count) / float(totalCount)
            output.append([base, ratio])
        return output
    def extractCountData(self, caseSensitive = True, formatForExcel = False):
	'''Used to get base counts in a format that can be pasted into excel. Counts returned are in the following order in a tab-delimitated string:
	A G C T M R W S Y K V H D B N a g c t m r w s y k v h d b n other
	'''
	def formatCounts(counts, caseSensitive = True):
            if caseSensitive:
                codes = ['A', 'G', 'C', 'T', 'M', 'R', 'W', 'S', 'Y', 'K', 'V', 'H', 'D', 'B', 'N', \
                         'a', 'g', 'c', 't', 'm', 'r', 'w', 's', 'y', 'k', 'v', 'h', 'd', 'b', 'n', 'other']
            else:
                codes = ['A', 'G', 'C', 'T', 'M', 'R', 'W', 'S', 'Y', 'K', 'V', 'H', 'D', 'B', 'N', 'other']                
            output = []
            for code in codes:
                output.append([code, 0])
            for char, count in counts:
                if caseSensitive == False:
                    char = char.upper()
                try:
                    output[codes.index(char)][1] += count
                except: #if the character is not recognized it is placed in the 'other' category 
                    output[-1][1] += count
            return output
        def formatCountsForExcel(counts):
            chars, counts = zip(*counts)
            return '\t'.join(map(str,counts))
	counts = formatCounts(self.baseCounts(), caseSensitive = caseSensitive)
	if formatForExcel:
            counts = formatCountsForExcel(counts)
	return counts
    def getUnalignedStartLength(self):
        firstCigar = self.cigarIter().next()
        if firstCigar[1] == 'S':
            return firstCigar[0]
        else:
            return 0
    def getUnalignedEndLength(self):
        lastCigar = list(self.cigarIter())[-1]
        if lastCigar[1] == 'S':
            return lastCigar[0]
        else:
            return 0
    def getUnalignedStart(self):
        firstCigar = self.cigarIter().next()
        if firstCigar[1] == 'S':
            return self.seq[:firstCigar[0]]
        else:
            return ''
    def getUnalignedEnd(self):
        lastCigar = list(self.cigarIter())[-1]
        if lastCigar[1] == 'S':
            return self.seq[:lastCigar[0]]
        else:
            return ''

class PileupAlignment(Alignment):
    '''Version 2.1'''
    def alignedStart(self):
        return self.start + self.padding
    def alignedEnd(self):
        return self.alignedStart() + len(self.alignedIndexs) - 1
    def relToAbsIndex(self, index):
        return index - self.alignedStart()
    def inRange(self, index):
        if self.alignedStart() <= index and self.alignedEnd() >= index: return True
        else: return False
    def indexIter(self, start = None, end = None):
        '''Version 1.0
        Returns the unaligned sequence index for aligned portions of the sequence and the cigar character one base at a time.
        An index of 'None' indicates that the base is an inserted spacer (e.g. deletion). 
        Output: (unaligned_sequence_index, cigar_letter)'''
        if start is None:
            baseIndex = 0
        else:
            baseIndex = self.relToAbsIndex(start)
        if end is None:
            while baseIndex < len(self.alignedIndexs):
                yield self.alignedIndexs[baseIndex]
                baseIndex += 1
        else:
            end = self.relToAbsIndex(end)
            if end >= len(self.alignedIndexs):
                end = len(self.alignedIndexs) - 1
            while baseIndex <= end:
                yield self.alignedIndexs[baseIndex]
                baseIndex += 1
    def selfIndexIter(self, start = None, end = None):
        for index, cigarType in PileupAlignment.indexIter(self, start, end):
            yield (self, index, cigarType)
    def refreshAlignment(self):
        self.alignedIndexs = list(Alignment.indexIter(self))
        #self.insertionIndexes = [index for index, letter in self.alignedIndexs if letter == 'I']
    def __initialize__(self, **kwargs):
        varDefaults = {'padding' : 0}
        for name, value in varDefaults.iteritems(): #For every new variable to be added to this instance..
            if name not in kwargs or kwargs[name] is None:
                kwargs[name] = value
        for name, value in kwargs.iteritems():
            setattr(self, name, kwargs[name])
        self.refreshAlignment()
    def __init__(self, seq, padding = None, **kwargs):
        if 'cigar' not in kwargs:
            kwargs['cigar'] = '%dM' % len(seq)
        Alignment.__init__(self, seq, **kwargs)
        args = {'padding' : padding}
        self.__initialize__(**args)
    @classmethod
    def fromAlignment(cls, alignment, **kwargs):
        '''Alternate constructor function that makes an instance of PileupAlignment using the information from an Alignment object.'''
        alignment.__class__ = PileupAlignment
        PileupAlignment.__initialize__(alignment, **kwargs)
        return alignment
    def __getitem__(self, index):
        '''Returns the base value at the specified distance from the start of the alignment. The index giving should include the effects of padding.'''        
        if self.alignedIndexs[index][0] is None:
            return cigarInsertTypes[self.alignedIndexs[index][1]] #if it is an inserted character
        else:
            return self.seq[self.alignedIndexs[index][0]]
    def getPerLetterAttribute(self, attributeName, index):
        if index is None:
            return 0
        else:
            return self._per_letter_annotations[attributeName][index]
    def getBase(self, index):
        '''Version 1.1
        Returns the base value at the reference index specified.'''
        index = self.relToAbsIndex(index)
        if index < 0:
            raise IndexError
        return self.__getitem__(index)
    def getCigarAtPos(self, index):
        '''Version 1.0
        Returns the cigar value at the reference index specified.'''
        index = self.relToAbsIndex(index)
        return self.alignedIndexs[index][1]
    def alignedSeq(self, start = None, end = None):
        '''Version 1.1
        Returns the aligned portions of the sequence.'''
        if start is None:
            start = 0
        if end is None:
            end  = len(self.alignedIndexs)
        return [self.__getitem__(index) for index in range(start, end)]
    def unpaddedAlignedSeq(self):
        return Alignment.alignedSeq(self)
    def identityCount(self, caseSensitive = True, reference = None):
        '''Version 1.0
        Returns the number of bases of the aligned sequence that match the reference. NOT TESTED'''
        if reference == None:
            reference = self.reference
        referenceIndex = self.alignedStart()
        matchCount = 0
        for queryBase in self.alignedSeq():
            referenceBase = reference.getBase(referenceIndex)
            if caseSensitive == False:
                queryBase = queryBase.upper()
                referenceBase = referenceBase.upper()
            if referenceBase == queryBase:
                matchCount += 1
            referenceIndex += 1
        return matchCount
    def substitutionCount(self, reference = None):
        '''Version 1.0
        Returns the number of bases that differ from the reference. Does not include indels or padding. NOT TESTED'''
        if reference == None:
            reference = self.reference
        referenceIndex = self.alignedStart()
        substitutionCount = 0
        for queryIndex, cigarLetter in self.indexIter():
            referenceBase = reference.getBase(referenceIndex)
            if cigarLetter == 'M' and referenceBase != self.seq[queryIndex]:
                substitutionCount += 1
            referenceIndex += 1
        return substitutionCount
    def insertionCount(self):
        '''Version 1.0
        Returns the number of insertions relative to the reference. Consecutive insertions are considered a single insertion. NOT TESTED'''
        return self.cigar.count('I')
    def deletionCount(self):
        '''Version 1.0
        Returns the number of deletion relative to the reference. Consecutive deletions are considered a single deletion. NOT TESTED'''
        return self.cigar.count('D')
    def insertionLength(self):
        '''Version 1.0
        Returns total length of all insertions. NOT TESTED'''
        return sum([length for length, letter in self.cigarIter() if letter == 'I'])
    def deletionLength(self):
        '''Version 1.0
        Returns total length of all deletions. NOT TESTED'''
        return sum([length for length, letter in self.cigarIter() if letter == 'D'])
    def ambiguousLength(self):
        '''Version 1.0
        Returns total length of all deletions. NOT TESTED'''
        return sum([length for length, letter in self.cigarIter() if letter == 'N'])
    def indelLength(self):
        '''Version 1.0
        Returns total length of all insertions and deletions. NOT TESTED'''
        return self.insertionLength() + self.deletionLength()
    def alignedLength(self):
        '''Version 1.0
        Returns the length of sections aligned to the referenced (not necesarily matching). NOT TESTED'''
        return sum([length for length, letter in self.cigarIter() if letter == 'M'])
    def identityProportion(self, caseSensitive = True, reference = None):
        '''Version 1.0
        Returns the ratio of the aligned sequence that matches the reference. NOT TESTED'''
        count = self.identityCount(caseSensitive = caseSensitive, reference = reference)
        length = self.alignedLength() + self.indelLength()
        print self.alignedLength(),  self.indelLength(), count
        return float(count) / length
    def alignedProportion(self):
        '''Version 1.0
        Returns the proportion of the referenced that sequence is aligned to. NOT TESTED'''
        count = self.alignedLength(caseSensitive = caseSensitive, reference = reference)
        return float(count) / self.alignedLength()

  
class Cluster(object):
    '''Version 2.1
    A collection of Alignments. Each alignment is treated independantly as if contigs aligned to a reference.'''
    def __init__(self, alignments = None, name = None):
        self.name = name
        if alignments is None: self.alignments = []
        else: self.alignments = alignments
    def indexIter(self, saveRefPadding = False):
        '''Verison 1.0'''
        deltas = [self.alignments[index].start - self.alignments[index - 1].start for index in range(1,len(self.alignments))] #a list of the difference between the start positions between adjacent reads
        generators = [self.alignments[0].selfIndexIter()]
        insertions = 0        
        for deltaIndex in range(0,len(deltas)):
            count = 0
            while count < deltas[deltaIndex]: #for every base until the start of the next read
                try: alignments, relBaseIndexes, cigarTypes = iterateGenerators(generators)
                except ValueError: alignments, relBaseIndexes, cigarTypes = (), (), ()
                yield (alignments, relBaseIndexes, cigarTypes)
                #if 'P' in cigarTypes or 'I' in cigarTypes: insertions += 1#insertions to reads do not have an index in the reference
                if 'I' in cigarTypes: insertions += 1#insertions to reads do not have an index in the reference
                else: count += 1
            if saveRefPadding: self.alignments[deltaIndex + 1].padding = insertions
            generators.append(self.alignments[deltaIndex + 1].selfIndexIter())
        while True: #continue iterating after all the reads have been encountered
            output = iterateGenerators(generators)
            if len(generators) == 0: break
            else: yield output
    def baseIter(self, start = None, end = None):
        '''Version 1.0
        Returns a list of bases for each position searched.'''
        for alignments, relBaseIndexes, cigarTypes in self.indexIter(pileupStart = start, pileupEnd = end):
            bases = []
            for alignment, relBaseIndex, cigarType in zip(alignments, relBaseIndexes, cigarTypes):
                if cigarType in cigarInsertTypes: bases.append(cigarInsertTypes[cigarType])
                else: bases.append(alignment.seq[relBaseIndex])
            yield bases
        
class Pileup(Cluster):
    '''Version 1.1'''
    def start(self):
        return self.alignments[0].alignedStart()
    def end(self):
        return max([alignment.alignedEnd() for alignment in self.alignments])
    def span(self):
        return self.end() - self.start() + 1
    def __len__(self):
        return self.span()
    def alignmentsInRange(self, start = None, end = None):
        '''Version 1.2
        Return a list of all the alignments that have at least one base in the specified range.'''
        if start is None: start = 0
        alignmentsInRange = []
        if end is None:
            for index in range(0, len(self.alignments)):
                if self.alignments[index].alignedEnd() < start: continue
                alignmentsInRange.append(index)
        else:
            for index in range(0, len(self.alignments)):
                if self.alignments[index].alignedEnd() < start: continue
                if self.alignments[index].alignedStart() > end: break
                alignmentsInRange.append(index)
        return alignmentsInRange
    def alignmentsWithIndex(self, pos):
        '''Version 1.0
        Return a list of all the alignments that have at least one base at the specified position.'''        
        return [index for index in range(0, len(self.alignments)) if pos >= self.alignments[index].alignedStart() and pos <= self.alignments[index].alignedEnd()]
    def indexIter(self, pileupStart = None, pileupEnd = None):
        '''Verison 2.0'''
        def getYield(generators):
            output = iterateGenerators(generators)
            if output == []: output = ((), (), ())
            return output            
        if pileupStart is None: pileupStart = self.start()
        if pileupEnd is None: pileupEnd = self.end()
        position = pileupStart
        alignmentIndexes = self.alignmentsInRange(pileupStart, pileupEnd)
        firstAlignmentIndexes = self.alignmentsWithIndex(pileupStart) #finds the set of alignments that have a base at the start position to initialize the iteration
        inbetweenIndexes = [index for index in alignmentIndexes if index not in firstAlignmentIndexes]
        generators = [self.alignments[index].selfIndexIter(start = pileupStart, end = pileupEnd) for index in firstAlignmentIndexes]
        if len(inbetweenIndexes) > 0:
            ##iterate from the start point to the start of the first Alignment that dosent have a base at the start position
            firstDelta = self.alignments[inbetweenIndexes[0]].alignedStart() - pileupStart
            for count in range(0, firstDelta): yield getYield(generators)
            position += firstDelta
            ##iterate through the sections between adjacent reads
            for currentIndex, nextIndex in zip(inbetweenIndexes[:-1], inbetweenIndexes[1:]): 
                delta = self.alignments[nextIndex].alignedStart() - self.alignments[currentIndex].alignedStart()
                generators.append(self.alignments[currentIndex].selfIndexIter(end = pileupEnd))
                for count in range(0, delta): yield getYield(generators) #for every base until the start of the next alignment
                position += delta
            generators.append(self.alignments[inbetweenIndexes[-1]].selfIndexIter(end = pileupEnd)) 
        ##iterate from the start of the last read to the end point
        if pileupEnd is None:
            output = getYield(generators)
            while output != ((), (), ()):
                yield output
                output = getYield(generators)
        else:
            lastDelta = pileupEnd - position + 1
            for count in range(0, lastDelta): yield getYield(generators)
    def padAlignments(self, removeExtraPadding = True):
        '''Version 1.1'''
        position = self.start()
        paddingToBeRemoved = []
        for alignments, relBaseIndexes, cigarTypes in Cluster.indexIter(self, saveRefPadding = True):
            if 'I' in cigarTypes:
                for alignment, cigarType in zip(alignments, cigarTypes):
                    insertIndex = alignment.relToAbsIndex(position)
                    if cigarType not in cigarExtraTypes:
                        alignment.alignedIndexs.insert(insertIndex, (None, 'P'))
            elif removeExtraPadding:
                for alignment, cigarType in zip(alignments, cigarTypes):
                    if cigarType == 'P':
                        paddingToBeRemoved.append([alignment, alignment.relToAbsIndex(position)]) 
            position += 1
        ##remove extra padding
        if removeExtraPadding:
            for alignment, index in reversed(paddingToBeRemoved):
                del alignment.alignedIndexs[index]
        ##replace padding in the sequence, at the start, with an offset of the start position
        for alignment in self.alignments: 
            if alignment.alignedIndexs[0] == (None, 'P'):
                del alignment.alignedIndexs[0]
                alignment.padding += 1
    def getCigarAtPos(self, index, alignments):
        return [alignment.getCigarAtPos(index) for alignment in alignments]
    def padPosition(self, position):
        for alignment in self.alignments: alignment.alignedIndexs.insert(position, (None, 'P'))
    def addAlignment(self, newAlignment, align = False, padAlignment = False):
        '''Version 1.0
        Adds an alignment to the pileup in the correct position.
            padAlignment: if True, then '''
        for index in range(0,len(self.alignments)):
            if newAlignment.start < self.alignments[index].start:
                self.alignments.insert(index, newAlignment)
                if padAlignment: self.padAlignment(index)
                return
        self.alignments.append(newAlignment)
        if padAlignment: self.padAlignment(len(self.alignments) - 1)
    def delAlignment(self, alignmentOrIndex):
        '''Version 1.0
        Deletes the specified alignment.'''
        if type(alignmentOrIndex) == int: del self.alignments[alignmentOrIndex]
        else:
            for index in range(0,len(self.alignments)):
                if self.alignments[index] is alignmentOrIndex:
                    del self.alignments[index]
                    return
    def __init__(self, alignments = None, name = None, padAlignments = True, startOffset = 0):
        self.name = name
        if alignments is None: self.alignments = []
        else: self.alignments = alignments
        for alignment in alignments:
            alignment.start += startOffset
            alignment.sortAttr = 'alignedStart'
        self.alignments.sort()
        if padAlignments: self.padAlignments()
    @classmethod
    def fromNucmer(cls, nucmerOutputPath, **kwargs):
        def deltaToCigar(deltas, start, end, length):
            '''Version 1.0
            Converts a delta series (what NUCMER outputs) to a cigar sequence (SAM format)'''
            if start != 1:
                cigar = [[start - 1, 'S']]
            else:
                cigar = []
            if len(deltas) == 0:
                cigar.append([end - start + 1, 'M'])
            currentAlignedLength = start
            deletionCount, insertionCount = 0, 0
            for delta in deltas: 
                if delta < 0:
                    indelType = 'I'
                    insertionCount += 1
                else:
                    indelType = 'D'
                    deletionCount += 1
                if abs(delta) == 1 and cigar[-1][1] == indelType:
                    cigar[-1][0] += 1
                else:
                    cigar += [[abs(delta) - 1, 'M'], [1, indelType]]
                currentAlignedLength += abs(delta)
            if len(deltas) > 0:
                alignedEndLength = end + deletionCount - currentAlignedLength
                cigar.append([alignedEndLength, 'M'])
            unalignedEndLength = length - end
            if unalignedEndLength > 0:
                cigar.append([unalignedEndLength, 'S'])
            return ''.join(['%d%s' % (part[0], part[1]) for part in cigar])
        ##Apply Nucmer alignment information to alignments
        try:
            alignments = kwargs['alignments']
        except KeyError:
            raise TypeError('Pileup.fromNucmer requires the keyword argument "alignments."') 
        for alignment in alignments: alignment.cigar = None
        alignmentsDict = dict([[alignment.id, [alignment]] for alignment in alignments])
        nucmerOutput = parseNucmer(nucmerOutputPath)
        if nucmerOutput is None: return None
        for queryName, referenceName, referenceLength, queryLength, alignmentStats, deltas in zip(*nucmerOutput):
            referenceStart, referenceEnd, queryStart, queryEnd = alignmentStats[:4]
            cigar = deltaToCigar(deltas, queryStart, queryEnd, queryLength)
            #print queryName, deltas, queryStart, queryEnd, queryLength, cigar
            if queryName in alignmentsDict:
                if alignmentsDict[queryName][0].cigar is not None: #if this is not the first instance of an alignment with this query
                    alignmentsDict[queryName].append(copy.deepcopy(alignmentsDict[queryName][0]))
                alignmentsDict[queryName][-1].cigar = cigar
                alignmentsDict[queryName][-1].start = referenceStart
                alignmentsDict[queryName][-1].refreshAlignment()
        kwargs['alignments'] = [alignment for alignments in alignmentsDict.values() for alignment in alignments if alignment.cigar is not None]   #combines alignments into one list
        ##make new Pileup instance
        instance = Pileup(**kwargs)
        return instance
    def makeConsensus(self, baseFilters = None, positionFilters = None, maskingFilters = None, maskingChar = 'N', IUPAC = True):
        '''Version 1.0'''
        consensus = []
        if baseFilters == None: baseFilters = []
        if positionFilters == None: positionFilters = []
        if maskingFilters == None: maskingFilters = []
        for positionData in self.indexIter():
            ##Apply base filters; ignores bases in individual alignments that do not pass all filters supplied
            positionData = zip(*positionData) #changes format from [[alignment, ...], [index, ...], [cigar, ...]] to [[alignment, index, cigar], ...]
            for baseFilter in baseFilters:
                positionData = baseFilter(positionData) #remove bases that dont pass filters 
            ##Apply position filters; excludes postions in the consensus that do not pass all filters supplied
            positionFilterResults = [positionFilter(positionData) for positionFilter in positionFilters]
            #if False in positionFilterResults:
            #    continue #if the position does not pass all filters, then it is not included in the consensus
            ##Apply masking filters; mask positons in the consensus that do not pass all filters supplied
            maskingFilterResults = [maskingFilter(positionData) for maskingFilter in maskingFilters]
            if False in maskingFilterResults:
                consensus.append(maskingChar)
                continue
            bases = []
            posDatLen = len(positionData) #############
            for read, index, cigar in positionData:
                if cigar in cigarInsertTypes:
                    bases.append(cigarInsertTypes[cigar])
                else:
                    try:
                        bases.append(read.seq[index])
                    except:
                        print read.id, index, cigar, read.cigar ##########
                        print 'len(positionData)', posDatLen #######
                        print 'len(read.seq)', len(read.seq)
                        raise
            if IUPAC:
                consensusBase = getIUPAC(bases, deletionCharacter = cigarInsertTypes['D'], paddingCharacter = cigarInsertTypes['P'], skippedCharacter = cigarInsertTypes['N'])
            else:
                consensusBase = getMajority(bases)
            consensus.append(consensusBase)
        
        return PileupAlignment(Seq(''.join(consensus)), start = self.start(), id=self.name)
        

###Input/Output Classes###
class AlignmentIO:
    '''Version 1.0'''
    @classmethod
    def parseSam(cls, text, qualityEncoding = None):
        '''Verison 1.1
        Alternate constructor function that makes an instance of alignment using the information from a sam file or string in sam format.'''
        if qualityEncoding == None:
            qualityEncoding = 'sanger'
        attributeOrder = ['id', 'flag', 'reference', 'start', 'quality', 'cigar', 'mate', 'mateStart'] #names of alignment atrributes in the order they appear in a sam file
        attributeType = [str, int, str, int, int, str, str, int]
        optionalTypeParsingFuncs = {'A':str, 'i':int, 'f':float, 'Z':str, 'H':str, 'B': str}
        data = text.strip().split('\t')
        for index in range(0,len(data)):
            if data[index] == '*':
                data[index] = None            
        kwargDict = {}
        seq = Seq(data[9])
        for attrName, attrType, columnData in zip(attributeOrder, attributeType, data[:8]):
            kwargDict[attrName] = attrType(columnData)
        if data[10] is not None:
            try:
                kwargDict['letter_annotations'] = {'phred_quality' : [phredConversion[qualityEncoding].index(score) for score in data[10]]}
            except ValueError:
                errorChars = ''.join([char for char in data[10] if char not in phredConversion[qualityEncoding]])
                raise ValueError('Cant parse quality sequence from read "%s": "%s". The following characters are invalid: %s' % (data[0], data[10], errorChars))
        kwargDict['annotations'] = {}
        for option in data[11:]:
            tag, optionType, value = option.split(':')
            kwargDict['annotations'][tag] = optionalTypeParsingFuncs[optionType](value)
        return Alignment(seq, **kwargDict)
    @classmethod
    def readSamFile(cls, path, qualityEncoding = None):
        '''Version 1.1'''
        with open(path, 'r') as handle:
            for line in handle: 
                if line[0] != '@':
                    break
            yield AlignmentIO.parseSam(line, qualityEncoding = qualityEncoding)
            for line in handle:
                yield AlignmentIO.parseSam(line, qualityEncoding = qualityEncoding)
    @classmethod
    def readBamFile(cls, path, qualityEncoding = None):
        '''Version 1.0'''
        process = subprocess.Popen(['samtools','view', path], stdout=subprocess.PIPE)
        while True:
            line = process.stdout.readline()
            if line != '':
                yield AlignmentIO.parseSam(line, qualityEncoding = qualityEncoding)
            else:
                raise StopIteration
                break
    @classmethod
    def writeFastaPileup(cls, alignments, handle, spacer = '_', includeUnalignedSequence = False):
        '''Version 1.0
        NOT TESTED'''
        offsets = [alignment.alignedStart() - alignment.getUnalignedStartLength() for alignment in alignments]
        smallestOffset = min(offsets)
        if smallestOffset < 0:
            offsetCorrection = abs(smallestOffset)
        else:
            offsetCorrection = 0
        for alignment in alignments:
            if includeUnalignedSequence:
                print alignment.id, alignment.start, alignment.alignedStart(), alignment.end(), alignment.padding, alignment.cigar
                unalignedStart = alignment.getUnalignedStart().lower()
                unalignedEnd = alignment.getUnalignedEnd().lower()
                sequence = unalignedStart + ''.join(alignment.alignedSeq()) + unalignedEnd
                offsetString = spacer * (alignment.alignedStart() - len(unalignedStart) + offsetCorrection)
            else:
                sequence = ''.join(alignment.alignedSeq())
                offsetString = spacer * (alignment.alignedStart() + offsetCorrection)
            handle.write('>%s\n%s%s\n' % (alignment.id, offsetString, sequence))                
    @classmethod
    def parse(cls, path, fileFormat, maxSize = None, qualityEncoding = None):
        '''Version 1.2'''
        formatParsers = {'sam' : cls.readSamFile, 'bam' : cls.readBamFile}
        fileFormat = fileFormat.lower()
        if fileFormat.lower() in formatParsers:
            if maxSize is None:
                for output in formatParsers[fileFormat](path, qualityEncoding = qualityEncoding):
                    yield output
            else:
                count = 1
                for output in formatParsers[fileFormat](path, qualityEncoding = qualityEncoding):
                    if count <= maxSize:
                        yield output
                    else:
                        break
                    count += 1
        else:
            for record in SeqIO.parse(path, fileFormat):
                yield Alignment.fromRecord(record)
    @classmethod
    def write(cls, alignments, handleOrPath, fileFormat, overwrite = False, includeUnalignedSequence = False):
        '''Version 1.0'''
        formatWriters = {'fasta-pileup' : cls.writeFastaPileup}
        if type(handleOrPath) == str:
            isHandle = True
            if overwrite:
                handleOrPath = open(handleOrPath, 'w')
            else:
                handleOrPath = open(handleOrPath, 'a')
        else: isHandle = False
        if fileFormat.lower() in formatWriters:
            formatWriters[fileFormat](alignments, handleOrPath, includeUnalignedSequence = includeUnalignedSequence)
        else:
            SeqIO.write(alignments, handleOrPath, fileFormat)
        if isHandle:
            handleOrPath.close()

class PileupAlignmentIO(AlignmentIO):
    '''Version 1.0'''
    @classmethod
    def parseSam(cls, text):
        return PileupAlignment.fromAlignment(AlignmentIO.parseSam(text))
    @classmethod
    def readSamFile(cls, handle):
        '''Version 1.0'''
        for alignment in AlignmentIO.readSamFile(handle): yield PileupAlignment.fromAlignment(alignment)

class PileupIO:
    '''Version 1.0'''
    @classmethod
    def readFastaFile(cls, filePath, referenceIndexes = None, includeReference = True, lowerCaseIsUnaligned = True, deletionCharacter =  cigarInsertTypes['D'],\
                      paddingCharacter = cigarInsertTypes['P'], skippedCharacter = cigarInsertTypes['N']):
        '''Version 1.0
        Parses an aligned fasta file into a Pileup object(s). If there is more than one pileup in a single file, every aligned
        sequence must follow its respective reference and precede the next reference/pileup. The index of each reference must
        be specified. if it isnt, it will be assumed that there is one reference and it is index 0. If the references indexes
        are specified and the first is not 0, and preceding sequences will be ignored. NOT TESTED'''
        if referenceIndexes is None:
            referenceIndexes = [0]
        referenceIndexes.sort()        
        with open(filePath, 'r') as handle:
             alignments = map(PileupAlignment.fromAlignment, map(Alignment.fromRecord, list(SeqIO.parse(handle, 'fasta')))) #parses the file into PileupAlignment objects
        sequencesPerReference = [referenceIndexes[i] - referenceIndexes[i - 1] - 1 for i in range(1,len(referenceIndexes))]
        sequencesPerReference.append(len(alignments) - referenceIndexes[-1] - 1)
        references = [alignments.pop(index) for index in reversed(referenceIndexes)] #separates the references from the alignments
        del alignments[:referenceIndexes[0]] #removes alignments before first reference
        for reference, alignmentCount in zip(references, sequencesPerReference):
            pileupAlignments = []
            if includeReference:
                reference.start, reference.end = 0, len(reference.seq)
                pileupAlignments.append(reference)
            for count in range(0, alignmentCount):
                alignment = alignments.pop(0)
                alignment = interpretFastaAlignment(alignment, reference, deletionCharacter = deletionCharacter[-1], paddingCharacter = paddingCharacter,\
                                                    skippedCharacter = skippedCharacter, lowerCaseIsUnaligned = lowerCaseIsUnaligned)
                pileupAlignments.append(alignment)
            yield Pileup(alignments = pileupAlignments, padAlignments = False, name = reference.id)

    @classmethod
    def readSam(cls, handle, applyPadding = True, alignPileups = True, group = True):
        '''Version 1.0'''
        ##Move past header
        #line = handle.readline()
        #while line != '' and line[0] == '@':
        #    header.append(line)
        #    line = handle.readline()
        ##Group alignments into pileups based on reference name 
        pileupAlignments = []
        headers = []
        #for alignment in PileupAlignmentIO.readSamFile(handle):
        for line in handle:
            if line[0] == '@': headers.append(line)
            else:
                pileupAlignments.append(PileupAlignmentIO.parseSam(line))
                break
        for line in handle:
            alignment = PileupAlignmentIO.parseSam(line)
            if len(pileupAlignments) > 0 and alignment.reference != pileupAlignments[-1].reference:
                yield Pileup(alignments = pileupAlignments, padAlignments = applyPadding,  name = pileupAlignments[0].reference)
                pileupAlignments = []
            pileupAlignments.append(alignment)
        yield Pileup(alignments = pileupAlignments, padAlignments = applyPadding, name = pileupAlignments[0].reference)
    @classmethod
    def readSamYasra(cls, handle, applyPadding = True):
        '''Version 1.0'''
        ##Move past header
        pileups = list(cls.readSam(handle, applyPadding))
        for pileup in pileups:
            start, end = pileup.alignments[0].reference.split('_')[-2:]
            print 'pileup.alignments[0].reference', pileup.alignments[0].reference
            print 'start, end', start, end
            print 'pileup.start()', pileup.start()
            print 'len(pileup.alignments)', len(pileup.alignments)
            print 'starts', [a.alignedStart() for a in pileup.alignments]
            for alignment in pileup.alignments: alignment.start += int(start)
            print 'pileup.start()', pileup.start()
        '''if applyPadding:
            allAlignments = []
            for pileup in pileups: allAlignments += pileup.alignments
            combinedPileup = Pileup(alignments = allAlignments, padAlignments = applyPadding)
            del combinedPileup'''
        for pileup in pileups: yield pileup
    '''@classmethod
    def readSamYasra(cls, handle, applyPadding = True):
        ''Version 1.1''
        ##Move past header
        pileups = list(cls.readSam(handle, False))
        finalHitsName = os.path.join(os.path.dirname(handle.name), 'final_hits' + os.path.basename(handle.name)[10:-3] + 'txt')
        finalHitsStarts = {}
        for line in open(finalHitsName,'r'):
            line = line.strip().split('\t')
            finalHitsStarts[line[3]] = int(line[1])
        for pileup in pileups:
            for alignment in pileup.alignments: alignment.start = finalHitsStarts[alignment.id]
        if applyPadding:
            allAlignments = []
            for pileup in pileups: allAlignments += pileup.alignments
            allAlignments.sort()
            combinedPileup = Pileup(alignments = allAlignments, padAlignments = applyPadding)
            del combinedPileup
        for pileup in pileups: yield pileup'''
    @classmethod
    def parse(cls, handleOrPath, fileFormat, maxSize = None, applyPadding = True):
        '''Version 1.0'''
        formatParsers = {'sam' : cls.readSam, 'sam-yasra' : cls.readSamYasra}
        fileFormat = fileFormat.lower()
        if type(handleOrPath) == str:
            isHandle = True
            handleOrPath = open(handleOrPath, 'r')
        else:
            isHandle = False
        for pileup in formatParsers[fileFormat](handleOrPath, applyPadding):
            yield pileup
        if isHandle:
            handleOrPath.close()
    @classmethod
    def writeFastaPileup(cls, pileups, handle, spacer = '_', includeUnalignedSequence = False):
        '''Version 1.0'''
        for pileup in pileups: AlignmentIO.writeFastaPileup(pileup.alignments, handle, spacer, includeUnalignedSequence = includeUnalignedSequence)
    @classmethod
    def write(cls, pileups, handleOrPath, fileFormat, overwrite = False, includeUnalignedSequence = False):
        '''Version 1.0
        improvements to be made:
            make parsers for fastq and sam'''
        formatWriters = {'fasta' : cls.writeFastaPileup}
        if type(handleOrPath) == str:
            isHandle = True
            if overwrite: handleOrPath = open(handleOrPath, 'w')
            else: handleOrPath = open(handleOrPath, 'a')
        else: isHandle = False
        if fileFormat.lower() in formatWriters: formatWriters[fileFormat](pileups, handleOrPath, includeUnalignedSequence = includeUnalignedSequence)
        else: SeqIO.write(pileups, handleOrPath, fileFormat)
        if isHandle: handleOrPath.close()

###Wrapper classes###
def dictToCommandLine(dictonary):
    commandLine = []
    for key, value in dictonary.iteritems():
        if value != False and value != None:
            commandLine.append('--' + key)
            if type(value) != bool:
                if type(value) != str: value = str(value)
                commandLine.append(value)
    return commandLine

def runNucmer(queryPath, referencePath, mum=False, mumreference=False, maxmatch=False, breaklen=200, mincluster=65, nodelta=False, depend=False,\
              diagfactor=0.12, noextend=False, forward=False, maxgap=90, help=False, minmatch=20, coords=False, nooptimize=False, prefix='out',\
              reverse=False, nosimplify=False, version=False):
    '''Version 1.0'''
    if mum == False and mumreference == False and maxmatch == False: mumreference = True #only one of the three options should be true
    options = locals()
    del options['queryPath'], options['referencePath']
    options = dictToCommandLine(options)
    nucmerCmndLine = ['nucmer'] + options + [referencePath,queryPath] #USAGE: nucmer  [options]  <Reference>  <Query>
    nucmerStdOut = open(os.path.join(os.getcwd(),'nucmer_standard_output.txt'), 'w')
    nucmerStdErr = open(os.path.join(os.getcwd(),'nucmer_standard_error.txt'), 'w')
    nucmerProcess = Popen(nucmerCmndLine, stdout=PIPE, stderr=PIPE)
    nucOutData, nucErrData = nucmerProcess.communicate()
    nucmerProcess.wait()
    nucmerStdOut.write(nucOutData)
    nucmerStdErr.write(nucErrData)
    nucmerStdOut.close()
    nucmerStdErr.close()
    if nucmerProcess.returncode != 0:
        raise NucmerError('Nucmer returned a non-zero code; it may have not completed successfully')
