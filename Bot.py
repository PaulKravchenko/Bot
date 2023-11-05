import pickle
import traceback
from pathlib import Path
from datetime import date,timedelta
from functools import reduce
from collections import UserDict

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
        

class AddressBook(UserDict):
    def __init__(self, file_name) -> None:
        self.__file_name = file_name
        super().__init__()

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
    
    def iterator(self, n=2):
        counter = 0
        values = list(self.data.values())
        while counter < len(values):
            yield list(map(lambda record: str(record), values[counter: counter + n]))
            counter += n
    
    def search_contacts(self, term:str) -> list:
        contacts = filter(lambda contact: contact.is_matching(term), self.data.values())
        return list(contacts)

    def __enter__(self):
        if Path(self.__file_name).exists():
            with open(self.__file_name, "rb") as file:
                self.data = pickle.load(file)
        return self
    
    def __exit__(self, exc_type:type, exc_val, exc_tb):                
        with open(self.__file_name, "wb") as file:
            pickle.dump(self.data, file)       
        if exc_type:
            tb = '\n'.join(traceback.format_tb(exc_tb))
            print(f"Exception detected\n{exc_type.__name__}: {exc_val}\n{tb}")            
        return True 

EXIT_COMMANDS = {"good bye", "bye", "exit", "quit", "stop"}
GREET_COMMANDS = {"hi", "hey", "hello", "howdy", "hi-ya", "howdy-do", "good morning", "good afternoon"}
GREETING_RESPONSES = {
    1: "Hello! How can I help you?",
    2: "Hey again! So how can I help you?",
    3: "Hey! Are you dumb or what? How can I help you?",
    4: "Are you kidding me? We have greeted 3 time now. Can I help you somehow?",
    5: "Fuuuck! Are you all right?",
    6: "Gotha, you might have Down syndrom... Hello, lovely human being :)",
    7: "Hellooo :)"
}

records: AddressBook = None

def input_error(*expected_args):
    def input_error_wrapper(func):
        def inner(*args):
            try:
                return func(*args)
            except IndexError:
                return f"Please enter {' and '.join(expected_args)}"
            except KeyError:
                return f"The record for contact {args[0]} not found. Try another contact or use help."
            except ValueError as error:
                if error.args:
                    return error.args[0]
                return f"Phone format '{args[1]}' is incorrect. Use digits only for phone number."
            except DuplicatedPhoneError as phone_error:
                return f"Phone number {phone_error.args[1]} already exists for contact {phone_error.args[0]}."
            except AttributeError:
                return f"Contact {args[0]} doesn't have birthday yet."
        return inner
    return input_error_wrapper

def capitalize_user_name(func):
    def inner(*args):
        new_args = list(args)
        new_args[0] = new_args[0].capitalize()
        return func(*new_args)
    return inner

def unknown_handler(*args) -> str:
    return f"Unknown command. Use help: \n{help_handler(*args)}"

def help_handler() -> str:
    help_txt = ""
    def inner(*args):
        global reads
        nonlocal help_txt
        if not help_txt:
            reads += 1
            with open("help.txt") as file:            
                help_txt = "".join(file.readlines())
        return help_txt
    return inner

@input_error("name", "phone")
@capitalize_user_name
def add_handler(*args) -> str:
    user_name = args[0]
    user_phones = args[1:]
    record = records.find(user_name, True)
    if not record:
        record = Record(user_name)
        for user_phone in user_phones:
            record.add_phone(user_phone)
        records.add_record(record)
        return f"New record added for {user_name} with phone number{'s' if len(user_phones) > 1 else ''}: {'; '.join(user_phones)}."
    else:
        response = []
        for user_phone in user_phones:
            record.add_phone(user_phone)
            response.append(f"New phone number {user_phone} for contact {user_name} added.")
        return "\n".join(response)

@input_error("name", "old_phone", "new_phone")
@capitalize_user_name
def change_handler(*args) -> str:
    user_name = args[0]
    old_phone = args[1]
    new_phone = args[2]
    record = records.find(user_name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number for {user_name} changed from {old_phone} to {new_phone}."

@input_error("name")
@capitalize_user_name    
def delete_handler(*args) -> str:
    user_name = args[0]
    user_phones = args[1:]
    if len(user_phones) >= 1:
        record = records.find(user_name)
        if record:
            response = []
            for user_phone in user_phones:
                record.remove_phone(user_phone)
                response.append(f"Phone number {user_phone} for contact {user_name} removed.")
            return "\n".join(response)
    else:
        if records.delete(user_name):
            return f"Record for contact {user_name} deleted."
        return f"Record for contact {user_name} not found."

@capitalize_user_name    
@input_error("name")
def birthday_handler(*args) -> str:
    user_name = args[0]
    user_birthday = args[1] if len(args) > 1 else None
    record = records.find(user_name)
    if record:
        if user_birthday:
            record.add_birthday(user_birthday)
            return f"Birthday {user_birthday} for contact {user_name} added."
        else:
            return f"{record.days_to_birthday()} days to the next {user_name}'s birthday ({record.birthday})."

@input_error([])
def greet_handler(num: int) -> str:
    def inner_greet(*args):
        nonlocal num
        num = num + 1 if num < 7 else 7
        return GREETING_RESPONSES[num]
    return inner_greet

@input_error("name")
@capitalize_user_name
def phone_handler(*args) -> str:
    user_name = args[0]
    record = records.find(user_name)
    if record:
        return "; ".join(map(lambda phone: str(phone), record.phones))    
    return f"Record for contact {user_name} not found."

@input_error("term")
def search_handler(*args) -> str:
    term = args[0]
    contacts = records.search_contacts(term)
    if contacts:
        return "\n".join(map(lambda contact: str(contact), contacts))    
    return f"No contacts found for '{term}'."

@input_error([])
def show_handler(*args) -> str:
    if args[0] == "all":
        return records.iterator()

COMMANDS = {
    "add": add_handler,
    "change": change_handler,
    "phone": phone_handler,
    "show": show_handler,
    "greet": greet_handler(0),
    "delete": delete_handler,
    "birthday": birthday_handler,
    "search": search_handler,
    "help": help_handler()
}

def command_parser(input:str) -> tuple:
    clauses = []
    command = ""
    if input in GREET_COMMANDS:
        command = "greet" 
    else:
        clauses = input.split()
        command = clauses[0]  
     
    args = []
    if len(clauses) > 0:
        args = clauses[1:]

    if command in COMMANDS.keys():
        return COMMANDS[command], args
    
    return unknown_handler, []

def main():
    global records
    with AddressBook("address_book.pkl") as book:
        records = book        
        while True:
            user_input = input(">>> ").lower()
            if user_input in EXIT_COMMANDS:
                print("Good bye!")
                break
            
            func, data = command_parser(user_input)
            result = func(*data)
            if isinstance(result, str):
                print(result)
            else:
                for i in result:                
                    print ("\n".join(i))
                    input("Press enter to show more records")     


if __name__ == "__main__":
    main()