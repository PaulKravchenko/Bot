import math
import re
import itertools as it
import functools

class Suggester:
    def __init__(self, words):
        self.__suggestions = {}
        for word in words:        
            self.__suggestions[word] = self.__parse_word(word)

    def __parse_word(self, word, total_length=None):
        chars = []
        for wrd in word.split():
            length = len(wrd)
            last_index = length -1
            weight = 1/total_length if total_length else 1/length
            chars = [(ch,weight) for ch in wrd]        
            half = math.ceil(length/2)        
            for i in range(half):
                boost = 1 - i * 0.1
                left = list(chars[i])
                right = list(chars[last_index-i])
                left[1] *= boost
                right[1] *= boost     
                chars[i] = tuple(left)
                chars[last_index-i] = tuple(right)
        return chars

    def suggest(self, word):
        chars = self.__parse_word(word)
        typo_solved = self.__resolve_typo(chars)
        if typo_solved:
            return typo_solved        
        matches = {}
        for sug_wrd in self.__suggestions.keys():
            mtch = self.__get_best_match(word, sug_wrd)
            if mtch:
                matches[mtch[0]] = mtch[1]
        result = {self.__rate_suggestion(chars, sug_chrs):sug_wrd for sug_wrd, sug_chrs in (matches.items() if matches else self.__suggestions.items())}
        #print(dict(sorted(result.items(),reverse=True)))
        return result[max(result.keys())]

    def __resolve_typo(self, chars):    
        sorted_chars = sorted(map(lambda ch: ch[0], chars))
        for sug_wrd, sug_chrs in self.__suggestions.items():
            if sorted(map(lambda ch: ch[0], sug_chrs)) == sorted_chars:
                return sug_wrd

    def __get_best_match(self, word, suggestion) -> tuple:
        part, full = (word, suggestion) if len(word) < len(suggestion) else (suggestion, word)        
        if part in full:
            return (suggestion, self.__parse_word(part, len(full)))
        return None


    def __rate_suggestion(self, chars, suggestion):
        rate_left = 0.0  
        rate_right = 0.0  
        last_index_chars = len(chars) - 1
        last_index_suggestion = len(suggestion) - 1    
        for i in range(min(len(chars),len(suggestion))):
            if chars[i][0] == suggestion[i][0]:            
                rate_left += min(chars[i][1], suggestion[i][1])
            if chars[last_index_chars - i][0] == suggestion[last_index_suggestion - i][0]:
                rate_right += min(chars[last_index_chars - i][1], suggestion[last_index_suggestion - i][1])
        return max(rate_left, rate_right)

