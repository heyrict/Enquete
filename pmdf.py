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
            expr = re.split(r"(?<!\\) +",l.strip())
            if len(expr) < 2:
                raise ValueError("Line `"+expr+"` too short")

            # convert "\ " back to " "
            for i in range(len(expr)):
                expr[i] = re.sub(r"\ "," ",expr[i])

            pmdf.getFieldAll(expr[0], expr[1], expr[2:] if len(expr) > 2 else "")
        return pmdf


class AbstractRestriction(object):
    def __init__(self, restrictionString):
        #if restrictionString == "": return
        self.confineList = []
        self.errstr = ""
        self._restriction = self.parse(restrictionString)

    def parse(self, restrictionString):
        return

    def fit(self, value):
        for rest in self._restriction:
            if self.satisfies(value, rest):
                return True
        return False


class PMStrRegexRestriction(AbstractRestriction):
    def parse(self, restrictionString):
        self.errstr = "doesn't match '%s'"%restrictionString
        return restrictionString

    def fit(self, value):
        return bool(re.match(self._restriction, value))


class PMNotNullRestriction(AbstractRestriction):
    def __init__(self):
        self.errstr = "cannot be null"
        self.confineList = []

    def fit(self, value):
        return (not value == "")


class FakeRestriction(AbstractRestriction):
    def fit(self, value):
        return True


class PMNumRangeRestriction(AbstractRestriction):
    QUARK = 1E-10

    def parse(self, restStr):
        self.errstr = "not in %s" % restStr
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
        self.errstr = "not in %s" % restStr
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

    def getFieldAll(self, fieldname, type_of_field, restrictions=[]):
        if fieldname in self.filter_dict:
            raise ValueError("Field "+fieldname+" already exists")

        type_of_field = self.caster_type(type_of_field)
        rest = []
        if restrictions == []: rest = [FakeRestriction("")]
        else:
            for restrictionString in restrictions:
                rest.append(self.getRestrictionFromString(restrictionString, type_of_field))

        self.field_list.append(fieldname)
        self.filter_dict[fieldname] = [type_of_field,rest]

    def getRestrictionFromString(self, restrictionString, type_of_field):
        if restrictionString.lower() == "not_null":
            return PMNotNullRestriction()

        if type_of_field in (int, float):
            try: return PMNumRangeRestriction(restrictionString)
            except: return PMStrRangeRestriction(restrictionString)
        else:
            if re.match("\[.*\]", restrictionString):
                return PMStrRangeRestriction(restrictionString)
            else:
                return PMStrRegexRestriction(restrictionString)

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
        for rest in self.filter_dict[fieldname][1]:
            if not rest.fit(data):
                errstr = rest.errstr if rest.errstr else "doesn't satisfy restriction"
                raise ValueError("Field `%s` %s"%(fieldname,errstr))
        return data

    def filter_all(self, ser):
        if isinstance(ser, dict):
            for f in ser:
                ser[f] = self.filter(f, ser[f])
            return ser
