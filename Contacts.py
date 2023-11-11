import pickle
import traceback
from pathlib import Path
from datetime import date,timedelta
from functools import reduce
from collections import UserDict
from Serialization import Serializable

class DuplicatedPhoneError(Exception):
    ...


class Field():
    def __init__(self, value: str):
        self.__value = value

    @property
    def value(self) -> str:
        return self.__value
   
    def _set_value(self, value) -> None:
        self.__value = value

    def __str__(self) -> str:
        return str(self.__value)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def is_matching(self, term) -> bool:
        return term in self.value.lower()


class Name(Field):
    ...


class Phone(Field):
    def __init__(self, value: str) -> None:
        self.value = value
    
    @property
    def value(self) -> str:
        return super().value

    @value.setter
    def value(self, value: str) -> None:
        super()._set_value(self.__validate(value))

    def __validate(self, value: str) -> str:
        value = reduce((lambda a, b: a.replace(b, "")), "+()-", value)        
        if value.isdigit() and len(value) == 10:
            return value
        else:
            raise ValueError(f"Phone number'{value}' is incorrect. Phone number should consist of 10 digits.")
        

class Birthday(Field):
    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def value(self) -> str:
        return super().value

    @property
    def date(self) -> date:
        return date(self.__year, self.__month, self.__day)
        
    @value.setter
    def value(self, value: str) -> None:
        self.__year, self.__month, self.__day = self.__validate(value)
        super()._set_value(f"{self.__day}-{self.__month}-{self.__year}")

    def __validate(self, value: str) -> tuple:
        separator = "." if "." in value else "/" if "/" in value else "-"
        date_parts = value.split(separator)
        if len(date_parts) == 3:
            day, month, year = date_parts[:]
            if day.isdigit() and month.isdigit() and year.isdigit():
                if date(int(year), int(month), int(day)):
                    return int(year), int(month), int(day)
        raise ValueError(f"Birthday '{value}' format is incorrect. Use DD-MM-YYYY format")

class Record:
    def __init__(self, name: str, phone=None, birthday=None) -> None:
        self.name = Name(name)
        self.phones = [Phone(phone)] if phone else []
        self.birthday = Birthday(birthday) if birthday else "Not set"

    def __str__(self) -> str:
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday}"
    
    def add_phone(self, phone: str) -> None: 
        existing_phone = self.find_phone(phone)
        if not existing_phone:
            self.phones.append(Phone(phone))
        else:
            raise DuplicatedPhoneError(self.name, phone)

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def days_to_birthday(self) -> int:
        next_birthday = self.birthday.date.replace(year=date.today().year)
        if next_birthday < date.today():
            next_birthday = next_birthday.replace(year=next_birthday.year+1)
        delta = next_birthday - date.today()
        return delta.days

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        existing_phone = self.find_phone(old_phone)
        if existing_phone:
            idx = self.phones.index(existing_phone)
            self.phones[idx] = Phone(new_phone)
        else:
            raise ValueError(f"Phone number {old_phone} not found for contact {self.name}.")
                
    def remove_phone(self, phone: str) -> None:
        existing_phone = self.find_phone(phone)
        if existing_phone:
            self.phones.remove(existing_phone)
        else:
            raise ValueError(f"Phone number {phone} not found for contact {self.name}.")
                            
    def find_phone(self, phone: str) -> Phone:
        existing_phone = list(filter(lambda p: p.value == phone, self.phones))
        if len(existing_phone) > 0:
            return existing_phone[0]
    
    def has_matching_phone (self, term:str) -> bool:
        phones = filter(lambda p: p.is_matching(term), self.phones)
        return list(phones)

    def is_matching (self, term:str) -> bool:        
        return self.name.is_matching(term) or self.has_matching_phone(term)
        

class AddressBook(UserDict, Serializable):
    def __init__(self, file_name) -> None:        
        UserDict.__init__(self)
        Serializable.__init__(self, file_name)

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str, suppress_error=False) -> Record:
        if name in self.data.keys():
            return self.data[name]
        if not suppress_error:
            raise KeyError

    def delete(self, name: str) -> Record:
        if name in self.data.keys():
            return self.data.pop(name)
    
    def iterator(self, n=2, contacts: list = None):
        counter = 0
        values = contacts or list(self.data.values())
        while counter < len(values):
            yield list(map(lambda record: str(record), values[counter: counter + n]))
            counter += n
    
    def search_contacts(self, term:str) -> list:
        contacts = filter(lambda contact: contact.is_matching(term), self.data.values())
        return list(contacts)
    
    def get_contacts_by_birthdays(self, days:int):
        contacts = filter(lambda contact: contact.days_to_birthday() <= days, self.data.values())
        return self.iterator(contacts=list(contacts))