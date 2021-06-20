def parse(regex, string):
    exist = False # If regex in string

    if len(regex) < 3:
        raise Exception('not a valid regex')

    if regex[0] != '/' and regex[-1] != '/':
        raise Exception('not a valid regex')

    return exist

class CharParser:

    def __init__(self, char):
        self.char = char

    def parse(self, string, index):
        return index < len(string) and string[index] == self.char, index+1, string[index]

class RangeCharParser:

    def __init__(self, range):
        if len(range) == 3 and range[1] == '-':
            if range[0] < range[2]:
                self.range = [range[0], range[2]]
            else:
                raise Exception('first char cannot be greater than last one')
        else:
            raise Exception('range must be: [char]-[char]')

    def parse(self, string, index):
        return string[index] >= self.range[0] and string[index] <= self.range[1], index+1, string[index]

class OrParser:

    def __init__(self, parser_1, parser_2):
        self.parser_1 = parser_1
        self.parser_2 = parser_2

    def parse(self, string, index):
        result_1, index_1, value_1 = self.parser_1(string, index)
        result_2, index_2, value_2 = self.parser_2(string, index)
        if result_1:
            index_2 = index_1
            value_2 = value_1
        print('OrParser: ' + str(result_1 or result_2))
        return result_1 or result_2, index_2, value_2

class ConcatParser:
    def __init__(self, parser_1, parser_2):
        self.parser_1 = parser_1
        self.parser_2 = parser_2

    def parse(self, string, index):
        result_1, index_1, value_1 = self.parser_1(string, index)
        result_2, index_2, value_2 = self.parser_2(string, index_1)
        print('ConcatParser: ' + str(result_1 and result_2))
        return result_1 and result_2, index_2, value_1 + value_2

class OneOrZeroParser:
    def __init__(self, parser):
        self.parser = parser

    def parse(self, string, index):
        result_1, index_1, value_1 = self.parser(string, index)
        if result_1:
            result_2, index_2, value_2 = self.parser(string, index_1)
            print('OneOrZeroParser :' + str(not result_2))
            return not result_2, index_1, value_1
        print('OneOrZeroParser :' + str(True))
        return True, index, ''

class AnyParser:
    def __init__(self, parser):
        self.parser = parser

    def parse(self, string, index):
        i = 0
        while len(string) > index + i and self.parser(string, index + i):
            i += 1
        print('AnyParser: ' + str(True))
        return True, index + i, string[index:index + i]

class NthParser:
    def __init__(self, parser, number):
        self.parser = parser
        self.number = number

    def parse(self, string, index):
        for i in range(self.number):
            result_1, index_1, value_1 = self.parser(string, index+i)
            if not result_1:
                print('NthParser: ' + str(result_1))
                return result_1, index_1, string[index:index_1]
        result_1, index_1, value_1 = self.parser(string, index+self.number)
        print('NthParser: ' + str(not result_1))
        return not result_1, index + self.number, string[index:index+self.number]

class ManyParser:
    def __init__(self, parser):
        self.parser = parser
        self.anyParser = AnyParser(self.parser)

    def parse(self, string, index):
        result_1, index_1, value_1 = self.parser(string, index)
        result_2, index_2, value_2 = self.anyParser.parse(string, index_1)
        print('ManyParser: ' + str(result_1 and result_2))
        return result_1 and result_2, index_2, value_1 + value_2

# test
# b(a|ou)t{2}o?n+

aParser = CharParser('a')
bParser = CharParser('b')
oParser = CharParser('o')
oMaybe = OneOrZeroParser(oParser.parse)
uParser = CharParser('u')
tParser = CharParser('t')
t2Parser = NthParser(tParser.parse, 2)
nParser = CharParser('n')
nMany = ManyParser(nParser.parse)
ouConcat = ConcatParser(oParser.parse, uParser.parse)
aouOr = OrParser(ouConcat.parse, aParser.parse)
onConcat = ConcatParser(oMaybe.parse, nMany.parse)
tonConcat = ConcatParser(t2Parser.parse, onConcat.parse)
aoutonConcat = ConcatParser(aouOr.parse, tonConcat.parse)
regex = ConcatParser(bParser.parse, aoutonConcat.parse)

print(regex.parse(input('input: '), 0))
