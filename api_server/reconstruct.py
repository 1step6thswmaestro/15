# -*- coding: utf-8 -*-

class MatchedFragment:
    
    def __init__(self, raw_text, morph_idx):
        self.s = morph_idx[0]
        self.e = morph_idx[1]
        self.text = raw_text
    
    
    def is_matched_with(self, morph_idx):
        return self.s <= morph_idx <= self.e


class ReconstructionMap:
    
    def __init__(self, raw_text, morphs):
        if isinstance(raw_text, list):
            self.text = raw_text
        else:
            self.text = raw_text.split()
        self.morphs = morphs
        self.matching = self.make_matching()
        
    
    def make_matching(self):
        p0 = 0; p1 = 0; last_p1 = -1; n = len(self.morphs); m = len(self.text)
        ret = []
        rtoken = self.text[p0]; ptoken = u''
        while p0 < m and p1 < n:
            if p1 < n and (len(rtoken) > len(ptoken) + 3 or len(ptoken) < 1):
                ptoken += u"".join([u"".join(x.split(u"/")[:-1]) for x in self.morphs[p1].replace("+", " ").split()])
                p1 += 1
            else:
                ret.append(MatchedFragment(rtoken, (last_p1+1, p1)))
                last_p1 = p1
                ptoken = u''
                p0 += 1
                if p0 < m:
                    rtoken = self.text[p0]
                    
        if len(ptoken) > 0:
            ret.append(MatchedFragment(rtoken, (last_p1+1, p1)))
            
        return ret
    
    
    def get_range(self, rng):
        for i, match in enumerate(self.matching):
            if match.is_matched_with(rng[0]):
                s = max(0, i - 2)
                
        for i, match in enumerate(self.matching):
            if match.is_matched_with(rng[1]):
                e = min(len(self.matching)-1, i + 2)
        
        return u" ".join([x.text for x in self.matching[s:e+1]])
