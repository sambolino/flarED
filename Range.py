""" Class for checking the parameter range constraint """
class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __str__(self):
        """ for help representation """
        return 'in range {0}, {1}'.format(self.start, self.end)
    def __repr__(self):
        """ for error representation """
        return '[{0}, {1}]'.format(self.start, self.end)
    def __eq__(self, other):
        return self.start <= other <= self.end
    def __contains__(self, item):
        return self.__eq__(item)
    def __iter__(self):
        return self
