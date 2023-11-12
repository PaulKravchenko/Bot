import re
from collections import UserList
from typing import Iterator
from datetime import datetime
from Serialization import Serializable

class Note:
    __tags_reg_exp = r"#\w+"

    def __init__(self, title: str, text: str):
        self.__title: str = None
        self.__tags = {}
        self.__text: str = None
        self.__modified: datetime.now
        self.title = title        
        self.text = text                      
    
    def __parse_tags(self, value):
        all_tags = re.findall(self.__tags_reg_exp, value)
        unique_tags = set(all_tags)
        self.__tags = {tag.removeprefix("#").lower():all_tags.count(tag) for tag in unique_tags}

    @property
    def text(self):
        return self.__text
    
    @text.setter
    def text(self, value):
        self.__text = value        
        self.__parse_tags(value)
        self.__modified = datetime.now
    
    @property
    def modified(self):
        return self.__modified
    
    @property
    def tags(self):
        return self.__tags
    
    @property
    def title(self):
        return self.__title
    
    @title.setter
    def title(self, value):
        self.__title = value

    def __str__(self) -> str:
        return f"{self.title}:\n\t{self.text}"

    def __repr__(self) -> str:
        return self.__str__()
    
    
class Notes (UserList, Serializable):
    def __init__(self, file_name) -> None:        
        UserList.__init__(self)
        Serializable.__init__(self, file_name)

    def add_note(self, note:Note):
        self.append(note)
    
    def edit_note(self, title:str, text:str):
        notes = list(filter(lambda note: title == note.title, self.data)) 
        if notes:
            notes[0].text = text
    
    def delete_note(self, title:str):
        notes = list(filter(lambda note: title == note.title, self.data)) 
        if notes:
            return self.data.pop(self.data.index(notes[0]))
    
    def search_notes(self, query:str): # "buy #car #birthday John john"
        tags = set(re.findall(r"#\w+", query))        
        terms = set(query.split()) - tags     
        tags = set([tag.removeprefix("#") for tag in tags])
        notes = self.data
        all_queried_notes = []
        all_tagged_notes = []
        if terms:
            for term in terms:
                all_queried_notes += list(filter(lambda note: term.lower() in note.title.lower() or term.lower() in note.text.lower(), notes))
            notes = list(set(all_queried_notes))
        if tags:            
            for tag in tags:                
                tagged_notes = list(filter(lambda note: tag.lower() in note.tags.keys(), notes))
                tagged_notes.sort(key=lambda note: note.tags[tag.lower()], reverse= True)
                all_tagged_notes += tagged_notes
            notes = all_tagged_notes        
        return self.iterator(notes=notes)
    
    def __getitem__(self, index):
        if isinstance(index, int):
            return super().__getitem__(index)
        
        notes = list(filter(lambda note: index == note.title, self.data)) 
        if notes:
            return notes[0]
    
    def iterator(self, n=2, notes: list = None):
        counter = 0
        values = notes or self.data
        while counter < len(values):
            yield list(map(lambda note: str(note), values[counter: counter + n]))
            counter += n

# notes = Notes()
# notes.add_note(Note("test", "My #name is Paul #name. I'm a #solution #architect"))
# notes.add_note(Note("test1", "My #name is Paul #name #name. I'm a #solution #architect"))
# notes.add_note(Note("test2", "My #name is Paul. I'm a #solution #architect"))
# notes.add_note(Note("test3", "My #name is Paul #name. I'm a #solution #solution #architect"))

# notes.edit_note("test2", "My #name is Paul")

# print(notes[0])
# print(notes["test2"])
# print(notes.search_notes("#name"))
# print(notes.search_notes("#solution"))
