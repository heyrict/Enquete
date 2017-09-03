# PMDF file parser ( basic parser)

import re


class PMDFParser(object):
    def __init__(self, filestr=""):
        if filestr == "": return
        with open(filestr, 'r') as f:
            self.fs = f.read()

    def fromstr(self, string):
        self.fs = string

    def parse(self):
        pmdf = PMDF()
        for l in self.fs.splitlines():
            expr = re.split(" +",l.strip(),2)
            if len(expr) < 2:
                raise ValueError("Line `"+expr+"` too short")
            pmdf.getField(expr[0], expr[1], expr[2] if len(expr) > 2 else "")
        return pmdf


class AbstractRestriction(object):
    def __init__(self, restrictionString):
        #if restrictionString == "": return
        self.confineList = []
        self._restriction = self.parse(restrictionString)

    def parse(self, restrictionString):
        return

    def fit(self, value):
        for rest in self._restriction:
            if self.satisfies(value, rest):
                return True
        return False


class FakeRestriction(AbstractRestriction):
    def fit(self, value):
        return True


class PMNumRangeRestriction(AbstractRestriction):
    QUARK = 1E-10

    def parse(self, restStr):
        restriction = []
        for pat in re.findall("[\[(][0-9]*,[0-9]*[)\]]",restStr):
            head, tail = pat.split(',')
            restriction.append([
                float(head[1:]) + self.QUARK * (head[0]=='('),
                float(tail[:-1]) - self.QUARK * (tail[-1]==')')])
        #print(restriction)
        return restriction

    def satisfies(self, value, one_rest):
        return one_rest[0] <= value <= one_rest[1]


class PMStrRangeRestriction(AbstractRestriction):
    def parse(self, restStr):
        self.confineList = eval(restStr)
        return self.confineList

    def fit(self, value):
        return value in self._restriction


class PMDF(object):
    '''
    Pre-Modified Data Filter.

    Storage:
        list of dict {<fieldname>: [<type>, <restriction>]}

    Methods:
        filter(fieldname, data):
            raises exception if data doesn't meet the restriction.
            returns the filtered data.
        filter_all(ser):
            filter all fields in a pandas Series.
            no filtering for fields not in restrictions
    '''
    def __init__(self, filterdict={}):
        self.filter_dict = filterdict
        self.field_list = []

    def getField(self, fieldname, type_of_field, restrictionString=""):
        if fieldname in self.filter_dict:
            raise ValueError("Field "+fieldname+" already exists")

        type_of_field = self.caster_type(type_of_field)
        rest = None
        if restrictionString == "": rest = FakeRestriction("")
        elif type_of_field in [int, float]:
            rest = PMNumRangeRestriction(restrictionString)
        else:
            rest = PMStrRangeRestriction(restrictionString)

        self.field_list.append(fieldname)
        self.filter_dict[fieldname] = [type_of_field,rest]

    def getRestriction(self, fieldname):
        if fieldname not in self.field_list: return None
        return self.filter_dict[fieldname][1]

    def caster_type(self, type_to_caster):
        if type_to_caster in ["int", "integer"]:
            return int
        elif type_to_caster in ["double", "float"]:
            return float
        else: return str

    def filter(self, fieldname, data):
        data = self.filter_dict[fieldname][0](data)
        if self.filter_dict[fieldname][1].fit(data):
            return data
        else:
            raise ValueError("Value %s doesn't satisfy restriction"%fieldname)

    def filter_all(self, ser):
        if isinstance(ser, dict):
            for f in ser:
                ser[f] = self.filter(f, ser[f])
            return ser
